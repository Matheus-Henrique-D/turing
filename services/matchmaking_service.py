"""
services/matchmaking_service.py
Serviço de Fila e Pareamento Multijogador em Tempo Real (Human vs Human).

Protocolo de Handshake Atômico com Retenção de Estado e Prevenção de Concorrência:
1. Pareamento cria a sessão e marca ambos com status='matched', ready_ack=0, ack_migrated=0.
   O pareamento roda dentro de BEGIN IMMEDIATE, então dois aparelhos nunca criam
   sessões diferentes para o mesmo par.
2. Cada aparelho confirma prontidão via confirm_ready(user_id, session_id).
   O UPDATE no banco utiliza bitwise OR no SQL: ready_ack = (ready_ack | ?).
   Bit 1 = Player 1 | Bit 2 = Player 2.
   O estado 'all_ready' ocorre RIGOROSAMENTE quando ready_ack == 3 (0b11).
3. Fim do Avanço Solitário: se o handshake estourar o timeout sem ambos confirmarem,
   a partida é cancelada e ambos retornam para status='waiting' na fila.
4. Retenção de Estado: o registro na fila só é removido quando AMBOS chamaram
   confirm_migrated (ack_migrated == 3).
"""

from datetime import datetime, timedelta
import random
from typing import Optional
import uuid
from core.database import get_db_connection
from core.config import ROUND_TOPICS, STATUS_ACTIVE

HEARTBEAT_TIMEOUT_SECONDS = 30
# Folga maior que antes (10s): os aparelhos consultam a cada 0.8s~2s e ainda
# há animações com sleep, então 10s cancelava pareamentos legítimos.
HANDSHAKE_TIMEOUT_SECONDS = 25.0


class MatchmakingService:

    @staticmethod
    def cleanup_stale_queue():
        """Remove entradas abandonadas com heartbeat expirado."""
        now = datetime.now()
        hb_threshold = (now - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()
        hs_threshold = (now - timedelta(seconds=HANDSHAKE_TIMEOUT_SECONDS)).isoformat()

        with get_db_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("""
            UPDATE matchmaking_queue
            SET status = 'cancelled'
            WHERE status = 'waiting' AND last_heartbeat < ?
            """, (hb_threshold,))

            cur = conn.execute("""
            SELECT DISTINCT matched_session_id
            FROM matchmaking_queue
            WHERE status = 'matched' AND ready_ack < 3
              AND (matched_at IS NOT NULL AND matched_at < ?)
            """, (hs_threshold,))
            stale_sessions = [r["matched_session_id"] for r in cur.fetchall() if r["matched_session_id"]]

            for sid in stale_sessions:
                conn.execute("DELETE FROM game_sessions WHERE id = ?", (sid,))
                conn.execute("""
                UPDATE matchmaking_queue
                SET status = 'waiting',
                    matched_session_id = NULL,
                    ready_ack = 0,
                    ack_migrated = 0,
                    matched_at = NULL
                WHERE matched_session_id = ?
                """, (sid,))

    @staticmethod
    def get_waiting_count() -> int:
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT COUNT(*) as total
            FROM matchmaking_queue
            WHERE status = 'waiting' AND last_heartbeat >= ?
            """, (threshold,))
            row = cursor.fetchone()
            return row["total"] if row else 0

    @classmethod
    def _create_shared_session(cls, conn, user_id: int, peer_user_id: int,
                               exclude_topics: Optional[list] = None) -> str:
        now = datetime.now().isoformat()
        available_topics = [t for t in ROUND_TOPICS if t not in (exclude_topics or [])]
        if not available_topics:
            available_topics = ROUND_TOPICS
        selected_topic = random.choice(available_topics)
        session_id = str(uuid.uuid4())
        pretend_ai_user_id = random.choice([user_id, peer_user_id])

        conn.execute("""
        INSERT INTO game_sessions
            (id, user_id, opponent_type, persona, topic, status, created_at,
             player2_id, is_multiplayer, pretend_ai_user_id, round_ready_ack, round_migrated_ack)
        VALUES (?, ?, 'HUMAN', 'jogador_real', ?, ?, ?, ?, 1, ?, 0, 0)
        """, (session_id, user_id, selected_topic, STATUS_ACTIVE, now, peer_user_id, pretend_ai_user_id))

        return session_id

    @classmethod
    def join_queue(cls, user_id: int, username: str,
                   exclude_topics: Optional[list] = None) -> dict:
        """
        Insere ou atualiza o usuário na fila. Se houver outro jogador aguardando,
        faz o match imediatamente (de forma serializada via BEGIN IMMEDIATE).
        """
        cls.cleanup_stale_queue()
        now = datetime.now().isoformat()
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()

        with get_db_connection() as conn:
            # Serializa: só um aparelho por vez decide pareamentos
            conn.execute("BEGIN IMMEDIATE")

            cursor = conn.execute(
                "SELECT * FROM matchmaking_queue WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            if existing and existing["status"] == "matched" and existing["matched_session_id"]:
                sess_row = conn.execute(
                    "SELECT status FROM game_sessions WHERE id = ?",
                    (existing["matched_session_id"],)).fetchone()
                if sess_row and sess_row["status"] == STATUS_ACTIVE:
                    return {"status": "matched", "session_id": existing["matched_session_id"]}
                conn.execute("DELETE FROM matchmaking_queue WHERE user_id = ?", (user_id,))

            peer = conn.execute("""
            SELECT * FROM matchmaking_queue
            WHERE status = 'waiting' AND user_id != ? AND last_heartbeat >= ?
            ORDER BY created_at ASC
            LIMIT 1
            """, (user_id, threshold)).fetchone()

            if peer:
                session_id = cls._create_shared_session(
                    conn, user_id, peer["user_id"], exclude_topics)

                conn.execute("""
                INSERT INTO matchmaking_queue
                    (user_id, username, status, matched_session_id, created_at, last_heartbeat,
                     ready_ack, ack_migrated, matched_at)
                VALUES (?, ?, 'matched', ?, ?, ?, 0, 0, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    status = 'matched',
                    matched_session_id = excluded.matched_session_id,
                    last_heartbeat = excluded.last_heartbeat,
                    ready_ack = 0,
                    ack_migrated = 0,
                    matched_at = excluded.matched_at
                """, (user_id, username, session_id, now, now, now))

                conn.execute("""
                UPDATE matchmaking_queue
                SET status = 'matched',
                    matched_session_id = ?,
                    last_heartbeat = ?,
                    ready_ack = 0,
                    ack_migrated = 0,
                    matched_at = ?
                WHERE user_id = ?
                """, (session_id, now, now, peer["user_id"]))

                return {"status": "matched", "session_id": session_id}

            conn.execute("""
            INSERT INTO matchmaking_queue
                (user_id, username, status, matched_session_id, created_at, last_heartbeat,
                 ready_ack, ack_migrated, matched_at)
            VALUES (?, ?, 'waiting', NULL, ?, ?, 0, 0, NULL)
            ON CONFLICT(user_id) DO UPDATE SET
                status = 'waiting',
                matched_session_id = NULL,
                last_heartbeat = excluded.last_heartbeat,
                ready_ack = 0,
                ack_migrated = 0,
                matched_at = NULL
            """, (user_id, username, now, now))

            return {"status": "waiting"}

    @classmethod
    def poll_queue_status(cls, user_id: int, username: str,
                          exclude_topics: Optional[list] = None) -> dict:
        """
        Atualiza o heartbeat e verifica o estado do handshake.
        Retorna status: waiting | matched | ready_pending | all_ready
        """
        now = datetime.now().isoformat()
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()

        with get_db_connection() as conn:
            # BEGIN IMMEDIATE ANTES de qualquer escrita: impede que dois aparelhos
            # criem sessões diferentes para o mesmo par ao mesmo tempo.
            conn.execute("BEGIN IMMEDIATE")

            conn.execute(
                "UPDATE matchmaking_queue SET last_heartbeat = ? WHERE user_id = ?",
                (now, user_id))

            entry = conn.execute(
                "SELECT * FROM matchmaking_queue WHERE user_id = ?", (user_id,)).fetchone()

            if entry:
                status = entry["status"]
                session_id = entry["matched_session_id"]

                if status == "matched" and session_id:
                    sess = conn.execute(
                        "SELECT user_id, player2_id, status FROM game_sessions WHERE id = ?",
                        (session_id,)).fetchone()

                    if not sess or sess["status"] != STATUS_ACTIVE:
                        conn.execute("""
                        UPDATE matchmaking_queue
                        SET status = 'waiting', matched_session_id = NULL,
                            ready_ack = 0, ack_migrated = 0, matched_at = NULL
                        WHERE user_id = ?
                        """, (user_id,))
                        return {"status": "waiting"}

                    current_ack = entry["ready_ack"] or 0

                    # Ambos confirmaram: libera a transição, independente de timeout
                    if current_ack == 3:
                        return {"status": "all_ready", "session_id": session_id}

                    # Timeout do handshake: ninguém avança sozinho
                    matched_at = entry["matched_at"]
                    if matched_at:
                        try:
                            elapsed = (datetime.now() - datetime.fromisoformat(matched_at)).total_seconds()
                            if elapsed > HANDSHAKE_TIMEOUT_SECONDS:
                                conn.execute("DELETE FROM game_sessions WHERE id = ?", (session_id,))
                                conn.execute("""
                                UPDATE matchmaking_queue
                                SET status = 'waiting', matched_session_id = NULL,
                                    ready_ack = 0, ack_migrated = 0, matched_at = NULL
                                WHERE matched_session_id = ?
                                """, (session_id,))
                                return {"status": "waiting", "cancelled_timeout": True}
                        except Exception:
                            pass

                    p_bit = 1 if user_id == sess["user_id"] else (2 if user_id == sess["player2_id"] else 0)
                    if p_bit and (current_ack & p_bit) != 0:
                        return {"status": "ready_pending", "session_id": session_id}

                    return {"status": "matched", "session_id": session_id}

                if status == "waiting":
                    peer = conn.execute("""
                    SELECT * FROM matchmaking_queue
                    WHERE status = 'waiting' AND user_id != ? AND last_heartbeat >= ?
                    ORDER BY created_at ASC
                    LIMIT 1
                    """, (user_id, threshold)).fetchone()

                    if peer:
                        new_sid = cls._create_shared_session(
                            conn, user_id, peer["user_id"], exclude_topics)
                        conn.execute("""
                        UPDATE matchmaking_queue
                        SET status = 'matched',
                            matched_session_id = ?,
                            last_heartbeat = ?,
                            ready_ack = 0,
                            ack_migrated = 0,
                            matched_at = ?
                        WHERE user_id IN (?, ?)
                        """, (new_sid, now, now, user_id, peer["user_id"]))
                        return {"status": "matched", "session_id": new_sid}

                    return {"status": "waiting"}
            # Sem registro, 'cancelled' ou 'matched' sem sessão: cai para fora do
            # bloco (liberando o lock) e reentra na fila.

        return cls.join_queue(user_id, username, exclude_topics)

    @classmethod
    def confirm_ready(cls, user_id: int, session_id: str) -> dict:
        """
        Seta atomicamente o bit de prontidão via bitwise OR nas duas pontas da sessão.
        Retorna {'all_ready': bool, 'ready_count': int}.
        """
        with get_db_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            sess = conn.execute(
                "SELECT user_id, player2_id FROM game_sessions WHERE id = ?",
                (session_id,)).fetchone()
            if not sess:
                return {"all_ready": False, "ready_count": 0}

            bit = 1 if user_id == sess["user_id"] else (2 if user_id == sess["player2_id"] else 0)
            if bit == 0:
                return {"all_ready": False, "ready_count": 0}

            conn.execute("""
            UPDATE matchmaking_queue
            SET ready_ack = (ready_ack | ?), last_heartbeat = ?
            WHERE matched_session_id = ? AND status = 'matched'
            """, (bit, datetime.now().isoformat(), session_id))

            row = conn.execute("""
            SELECT ready_ack FROM matchmaking_queue
            WHERE user_id = ? AND matched_session_id = ?
            """, (user_id, session_id)).fetchone()

            current_mask = (row["ready_ack"] if row else 0) & 3
            return {"all_ready": current_mask == 3,
                    "ready_count": bin(current_mask).count("1")}

    @classmethod
    def confirm_migrated(cls, user_id: int, session_id: str):
        """
        Registra que este aparelho já está na tela do jogo. O registro na fila só
        é apagado quando AMBOS migraram (ack_migrated == 3).
        """
        with get_db_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            sess = conn.execute(
                "SELECT user_id, player2_id FROM game_sessions WHERE id = ?",
                (session_id,)).fetchone()
            if not sess:
                return

            bit = 1 if user_id == sess["user_id"] else (2 if user_id == sess["player2_id"] else 0)
            if bit == 0:
                return

            conn.execute("""
            UPDATE matchmaking_queue
            SET ack_migrated = (ack_migrated | ?)
            WHERE matched_session_id = ?
            """, (bit, session_id))

            row = conn.execute("""
            SELECT ack_migrated FROM matchmaking_queue
            WHERE matched_session_id = ? LIMIT 1
            """, (session_id,)).fetchone()

            if row and (row["ack_migrated"] & 3) == 3:
                conn.execute("DELETE FROM matchmaking_queue WHERE matched_session_id = ?", (session_id,))

    @staticmethod
    def leave_queue(user_id: int):
        """Remove o usuário da fila quando ele cancela ou sai da fila."""
        with get_db_connection() as conn:
            conn.execute("DELETE FROM matchmaking_queue WHERE user_id = ?", (user_id,))

    @staticmethod
    def force_leave_queue(user_id: int):
        """Remoção explícita ao cancelar busca antes de qualquer pareamento."""
        with get_db_connection() as conn:
            conn.execute("DELETE FROM matchmaking_queue WHERE user_id = ?", (user_id,))

    @staticmethod
    def has_played_real_human(user_id: int, recent_limit: int = 4) -> bool:
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT COUNT(*) as count
            FROM game_sessions
            WHERE (user_id = ? OR player2_id = ?)
              AND is_multiplayer = 1
            ORDER BY created_at DESC
            LIMIT ?
            """, (user_id, user_id, recent_limit))
            row = cursor.fetchone()
            return (row["count"] > 0) if row else False