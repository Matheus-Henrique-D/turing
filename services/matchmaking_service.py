"""
services/matchmaking_service.py
Serviço de Fila e Pareamento Multijogador em Tempo Real (Human vs Human).

Implementa um sistema de Double-Handshake para garantir que ambos os dispositivos
avancem para a partida de forma SIMULTÂNEA, eliminando race conditions e dessincronia:

  Fluxo:
  1. Jogador entra na fila → status='waiting', ready_ack=0
  2. Par é encontrado    → ambos ficam status='matched', ready_ack=0
  3. Cada dispositivo chama confirm_ready() ao detectar o match →
       ready_ack incrementa atomicamente (0→1 ou 1→2)
  4. poll_queue_status() retorna all_ready=True SOMENTE quando ready_ack_total == 2
  5. Apenas então ambos os dispositivos avançam para a partida
"""

from datetime import datetime, timedelta
import random
from typing import Optional
import uuid
from core.database import get_db_connection
from core.config import ROUND_TOPICS, STATUS_ACTIVE
from models.session import GameSession, SessionRepository

HEARTBEAT_TIMEOUT_SECONDS = 30
# Tempo máximo (segundos) que o sistema aguarda o segundo dispositivo confirmar
# o handshake antes de forçar a transição (evita travamento por aba fechada)
HANDSHAKE_TIMEOUT_SECONDS = 8


class MatchmakingService:

    # ──────────────────────────────────────────────────────────────────────────
    # MANUTENÇÃO DA FILA
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def cleanup_stale_queue():
        """Remove entradas antigas cujos clientes fecharam a aba ou desconectaram."""
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()
        with get_db_connection() as conn:
            conn.execute("""
            UPDATE matchmaking_queue
            SET status = 'cancelled'
            WHERE status = 'waiting' AND last_heartbeat < ?
            """, (threshold,))

    @staticmethod
    def get_waiting_count() -> int:
        """Retorna o número de jogadores ativos aguardando na fila."""
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT COUNT(*) as total
            FROM matchmaking_queue
            WHERE status = 'waiting' AND last_heartbeat >= ?
            """, (threshold,))
            row = cursor.fetchone()
            return row["total"] if row else 0

    # ──────────────────────────────────────────────────────────────────────────
    # CRIAÇÃO DE SESSÃO COMPARTILHADA (uso interno)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _create_shared_session(conn, user_id: int, peer_user_id: int,
                               exclude_topics: Optional[list] = None) -> str:
        """
        Cria a game_session compartilhada e retorna o session_id.
        Deve ser chamado dentro de um bloco 'with get_db_connection()'.
        """
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
             player2_id, is_multiplayer, pretend_ai_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, user_id, "HUMAN", "jogador_real", selected_topic,
              STATUS_ACTIVE, now, peer_user_id, 1, pretend_ai_user_id))

        return session_id

    # ──────────────────────────────────────────────────────────────────────────
    # ENTRAR NA FILA
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def join_queue(cls, user_id: int, username: str,
                   exclude_topics: Optional[list] = None) -> dict:
        """
        Insere/atualiza o usuário na fila e tenta parear imediatamente.
        Retorna dict com 'status' ('waiting' | 'matched') e opcionalmente 'session_id'.
        """
        cls.cleanup_stale_queue()
        now = datetime.now().isoformat()
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()

        with get_db_connection() as conn:
            # Verifica se já está pareado em sessão ativa
            cursor = conn.execute(
                "SELECT * FROM matchmaking_queue WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            if existing and existing["status"] == "matched" and existing["matched_session_id"]:
                sess_cur = conn.execute(
                    "SELECT status FROM game_sessions WHERE id = ?",
                    (existing["matched_session_id"],))
                sess_row = sess_cur.fetchone()
                if sess_row and sess_row["status"] == STATUS_ACTIVE:
                    return {"status": "matched", "session_id": existing["matched_session_id"]}
                else:
                    conn.execute(
                        "DELETE FROM matchmaking_queue WHERE user_id = ?", (user_id,))

            # Tenta parear com outro jogador disponível
            cursor = conn.execute("""
            SELECT * FROM matchmaking_queue
            WHERE status = 'waiting' AND user_id != ? AND last_heartbeat >= ?
            ORDER BY created_at ASC
            LIMIT 1
            """, (user_id, threshold))
            peer = cursor.fetchone()

            if peer:
                session_id = cls._create_shared_session(
                    conn, user_id, peer["user_id"], exclude_topics)

                # Ambos marcados como 'matched', ready_ack=0 (handshake pendente)
                conn.execute("""
                INSERT INTO matchmaking_queue
                    (user_id, username, status, matched_session_id, created_at, last_heartbeat, ready_ack)
                VALUES (?, ?, 'matched', ?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    status = 'matched',
                    matched_session_id = excluded.matched_session_id,
                    last_heartbeat = excluded.last_heartbeat,
                    ready_ack = 0
                """, (user_id, username, session_id, now, now))

                conn.execute("""
                UPDATE matchmaking_queue
                SET status = 'matched', matched_session_id = ?, last_heartbeat = ?, ready_ack = 0
                WHERE user_id = ?
                """, (session_id, now, peer["user_id"]))

                return {"status": "matched", "session_id": session_id}

            # Sem par: entra/permanece na fila como 'waiting'
            conn.execute("""
            INSERT INTO matchmaking_queue
                (user_id, username, status, matched_session_id, created_at, last_heartbeat, ready_ack)
            VALUES (?, ?, 'waiting', NULL, ?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                status = 'waiting',
                matched_session_id = NULL,
                last_heartbeat = excluded.last_heartbeat,
                ready_ack = 0
            """, (user_id, username, now, now))

            return {"status": "waiting"}

    # ──────────────────────────────────────────────────────────────────────────
    # HANDSHAKE: CONFIRMAR QUE ESTE DISPOSITIVO ESTÁ PRONTO
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def confirm_ready(cls, user_id: int, session_id: str) -> dict:
        """
        Chamado por cada dispositivo assim que ele detecta o match.
        Incrementa ready_ack atomicamente (máx 1 por usuário).
        Retorna {'all_ready': bool, 'ready_count': int}.

        - Se all_ready=True: AMBOS os dispositivos confirmaram → pode avançar.
        - Se all_ready=False: aguardar até poll_queue_status retornar all_ready=True.
        """
        now = datetime.now().isoformat()
        with get_db_connection() as conn:
            # Marca ESTE usuário como pronto (ready_ack=1 no registro dele)
            conn.execute("""
            UPDATE matchmaking_queue
            SET ready_ack = 1, last_heartbeat = ?
            WHERE user_id = ? AND matched_session_id = ? AND ready_ack = 0
            """, (now, user_id, session_id))

            # Conta quantos dos dois jogadores desta sessão já confirmaram
            cursor = conn.execute("""
            SELECT COUNT(*) as cnt
            FROM matchmaking_queue
            WHERE matched_session_id = ? AND ready_ack = 1 AND status = 'matched'
            """, (session_id,))
            row = cursor.fetchone()
            ready_count = row["cnt"] if row else 0

        return {"all_ready": ready_count >= 2, "ready_count": ready_count}

    # ──────────────────────────────────────────────────────────────────────────
    # POLLING PERIÓDICO (chamado a cada tick do autorefresh)
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def poll_queue_status(cls, user_id: int, username: str,
                          exclude_topics: Optional[list] = None) -> dict:
        """
        Atualiza o heartbeat e verifica o estado da fila para este usuário.

        Retorna dict com 'status':
          - 'waiting'        → ainda procurando par
          - 'matched'        → par encontrado, aguardando handshake
          - 'ready_pending'  → este dispositivo já confirmou, aguardando o par
          - 'all_ready'      → AMBOS confirmaram: pode avançar para a partida
        Inclui 'session_id' quando status != 'waiting'.
        """
        now = datetime.now().isoformat()
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()

        with get_db_connection() as conn:
            # Atualiza heartbeat
            conn.execute("""
            UPDATE matchmaking_queue SET last_heartbeat = ? WHERE user_id = ?
            """, (now, user_id))

            cursor = conn.execute(
                "SELECT * FROM matchmaking_queue WHERE user_id = ?", (user_id,))
            entry = cursor.fetchone()

            if not entry:
                # Entrada removida externamente: retorna ao join
                pass

            elif entry["status"] == "matched" and entry["matched_session_id"]:
                session_id = entry["matched_session_id"]

                # Verifica se a sessão ainda existe e está ativa
                sess_cur = conn.execute(
                    "SELECT status FROM game_sessions WHERE id = ?", (session_id,))
                sess_row = sess_cur.fetchone()
                if not sess_row or sess_row["status"] != STATUS_ACTIVE:
                    conn.execute(
                        "DELETE FROM matchmaking_queue WHERE user_id = ?", (user_id,))
                    return {"status": "waiting"}

                # Conta quantos jogadores desta sessão confirmaram o handshake
                ack_cur = conn.execute("""
                SELECT COUNT(*) as cnt
                FROM matchmaking_queue
                WHERE matched_session_id = ? AND ready_ack = 1 AND status = 'matched'
                """, (session_id,))
                ack_row = ack_cur.fetchone()
                ready_count = ack_row["cnt"] if ack_row else 0

                # Timeout de handshake: se o 2º dispositivo demorou demais, força avanço
                my_ack = entry["ready_ack"] if "ready_ack" in entry.keys() else 0
                matched_at = entry["last_heartbeat"]
                try:
                    matched_dt = datetime.fromisoformat(matched_at)
                    handshake_elapsed = (datetime.now() - matched_dt).total_seconds()
                except Exception:
                    handshake_elapsed = 0

                if ready_count >= 2:
                    return {"status": "all_ready", "session_id": session_id}

                # Forçar avanço se este já confirmou e o par sumiu (timeout)
                if my_ack == 1 and handshake_elapsed > HANDSHAKE_TIMEOUT_SECONDS:
                    return {"status": "all_ready", "session_id": session_id,
                            "forced": True}

                if my_ack == 1:
                    return {"status": "ready_pending", "session_id": session_id,
                            "ready_count": ready_count}

                return {"status": "matched", "session_id": session_id}

            elif entry["status"] == "waiting":
                # Tenta parear se outro jogador entrou
                cursor = conn.execute("""
                SELECT * FROM matchmaking_queue
                WHERE status = 'waiting' AND user_id != ? AND last_heartbeat >= ?
                ORDER BY created_at ASC
                LIMIT 1
                """, (user_id, threshold))
                peer = cursor.fetchone()

                if peer:
                    session_id = cls._create_shared_session(
                        conn, user_id, peer["user_id"], exclude_topics)

                    conn.execute("""
                    UPDATE matchmaking_queue
                    SET status = 'matched', matched_session_id = ?,
                        last_heartbeat = ?, ready_ack = 0
                    WHERE user_id IN (?, ?)
                    """, (session_id, now, user_id, peer["user_id"]))

                    return {"status": "matched", "session_id": session_id}

                return {"status": "waiting"}

        # Se não havia entrada, executa join_queue
        return cls.join_queue(user_id, username, exclude_topics)

    # ──────────────────────────────────────────────────────────────────────────
    # SAIR DA FILA
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def leave_queue(user_id: int):
        """Remove o usuário da fila de espera."""
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM matchmaking_queue WHERE user_id = ?", (user_id,))

    # ──────────────────────────────────────────────────────────────────────────
    # UTILITÁRIOS
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def has_played_real_human(user_id: int, recent_limit: int = 4) -> bool:
        """
        Verifica se o usuário já enfrentou outro humano real nas últimas N partidas.
        """
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
