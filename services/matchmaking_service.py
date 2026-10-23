"""
services/matchmaking_service.py
Serviço de Fila e Pareamento Multijogador em Tempo Real (Human vs Human).
Gerencia a fila de espera, batimento cardíaco (heartbeat) e criação de salas compartilhadas.
"""

from datetime import datetime, timedelta
import random
from typing import Optional, Tuple
import uuid
from core.database import get_db_connection
from core.config import ROUND_TOPICS, STATUS_ACTIVE
from models.session import GameSession, SessionRepository

HEARTBEAT_TIMEOUT_SECONDS = 30


class MatchmakingService:
    @staticmethod
    def cleanup_stale_queue():
        """Remove ou cancela entradas antigas cujos clientes fecharam a aba ou desconectaram."""
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()
        with get_db_connection() as conn:
            conn.execute("""
            UPDATE matchmaking_queue
            SET status = 'cancelled'
            WHERE status = 'waiting' AND last_heartbeat < ?
            """, (threshold,))

    @staticmethod
    def get_waiting_count() -> int:
        """Retorna o número de jogadores ativos atualmente aguardando na fila."""
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
    def join_queue(cls, user_id: int, username: str, exclude_topics: Optional[list] = None) -> dict:
        """
        Insere ou atualiza o usuário na fila de espera e tenta parear imediatamente
        caso já haja outro jogador aguardando.
        """
        cls.cleanup_stale_queue()
        now = datetime.now().isoformat()
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()

        with get_db_connection() as conn:
            # 1. Verifica se já está pareado em alguma sessão recente
            cursor = conn.execute("""
            SELECT * FROM matchmaking_queue WHERE user_id = ?
            """, (user_id,))
            existing = cursor.fetchone()
            if existing and existing["status"] == "matched" and existing["matched_session_id"]:
                return {
                    "status": "matched",
                    "session_id": existing["matched_session_id"]
                }

            # 2. Busca outro jogador disponível na fila
            cursor = conn.execute("""
            SELECT * FROM matchmaking_queue
            WHERE status = 'waiting' AND user_id != ? AND last_heartbeat >= ?
            ORDER BY created_at ASC
            LIMIT 1
            """, (user_id, threshold))
            peer = cursor.fetchone()

            if peer:
                # MATCH ENCONTRADO! Cria sessão compartilhada na mesma conexão
                available_topics = [t for t in ROUND_TOPICS if t not in (exclude_topics or [])]
                if not available_topics:
                    available_topics = ROUND_TOPICS
                selected_topic = random.choice(available_topics)
                session_id = str(uuid.uuid4())
                pretend_ai_user_id = random.choice([user_id, peer["user_id"]])

                # Insere sessão multijogador com missão secreta sorteada para 1 dos humanos
                conn.execute("""
                INSERT INTO game_sessions (id, user_id, opponent_type, persona, topic, status, created_at, player2_id, is_multiplayer, pretend_ai_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (session_id, user_id, "HUMAN", "jogador_real", selected_topic, STATUS_ACTIVE, now, peer["user_id"], 1, pretend_ai_user_id))

                # Atualiza ambos para 'matched'
                conn.execute("""
                INSERT INTO matchmaking_queue (user_id, username, status, matched_session_id, created_at, last_heartbeat)
                VALUES (?, ?, 'matched', ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    status = 'matched',
                    matched_session_id = excluded.matched_session_id,
                    last_heartbeat = excluded.last_heartbeat
                """, (user_id, username, session_id, now, now))

                conn.execute("""
                UPDATE matchmaking_queue
                SET status = 'matched', matched_session_id = ?, last_heartbeat = ?
                WHERE user_id = ?
                """, (session_id, now, peer["user_id"]))

                return {
                    "status": "matched",
                    "session_id": session_id
                }

            # Sem par no momento: entra na fila como 'waiting'
            conn.execute("""
            INSERT INTO matchmaking_queue (user_id, username, status, matched_session_id, created_at, last_heartbeat)
            VALUES (?, ?, 'waiting', NULL, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                status = 'waiting',
                matched_session_id = NULL,
                last_heartbeat = excluded.last_heartbeat
            """, (user_id, username, now, now))

            return {
                "status": "waiting"
            }

    @classmethod
    def poll_queue_status(cls, user_id: int, username: str, exclude_topics: Optional[list] = None) -> dict:
        """
        Chamado periodicamente (ex: a cada 1s pelo autorefresh do Streamlit).
        Atualiza o batimento cardíaco e verifica se o jogador foi pareado.
        """
        now = datetime.now().isoformat()
        threshold = (datetime.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()

        with get_db_connection() as conn:
            # Atualiza batimento cardíaco do usuário
            conn.execute("""
            UPDATE matchmaking_queue
            SET last_heartbeat = ?
            WHERE user_id = ?
            """, (now, user_id))

            cursor = conn.execute("""
            SELECT * FROM matchmaking_queue WHERE user_id = ?
            """, (user_id,))
            entry = cursor.fetchone()
            if not entry:
                # Se não tem entrada, tenta join_queue fora deste bloco
                pass
            elif entry["status"] == "matched" and entry["matched_session_id"]:
                return {
                    "status": "matched",
                    "session_id": entry["matched_session_id"]
                }
            elif entry["status"] == "waiting":
                # Tenta parear se outro jogador acabou de entrar
                cursor = conn.execute("""
                SELECT * FROM matchmaking_queue
                WHERE status = 'waiting' AND user_id != ? AND last_heartbeat >= ?
                ORDER BY created_at ASC
                LIMIT 1
                """, (user_id, threshold))
                peer = cursor.fetchone()

                if peer:
                    available_topics = [t for t in ROUND_TOPICS if t not in (exclude_topics or [])]
                    if not available_topics:
                        available_topics = ROUND_TOPICS
                    selected_topic = random.choice(available_topics)
                    session_id = str(uuid.uuid4())
                    pretend_ai_user_id = random.choice([user_id, peer["user_id"]])

                    conn.execute("""
                    INSERT INTO game_sessions (id, user_id, opponent_type, persona, topic, status, created_at, player2_id, is_multiplayer, pretend_ai_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (session_id, user_id, "HUMAN", "jogador_real", selected_topic, STATUS_ACTIVE, now, peer["user_id"], 1, pretend_ai_user_id))

                    conn.execute("""
                    UPDATE matchmaking_queue
                    SET status = 'matched', matched_session_id = ?, last_heartbeat = ?
                    WHERE user_id IN (?, ?)
                    """, (session_id, now, user_id, peer["user_id"]))

                    return {
                        "status": "matched",
                        "session_id": session_id
                    }

                return {"status": "waiting"}

        # Se não havia entrada, executa join_queue
        return cls.join_queue(user_id, username, exclude_topics)

    @staticmethod
    def leave_queue(user_id: int):
        """Remove o usuário da fila de espera."""
        with get_db_connection() as conn:
            conn.execute("""
            DELETE FROM matchmaking_queue WHERE user_id = ?
            """, (user_id,))

    @staticmethod
    def has_played_real_human(user_id: int, recent_limit: int = 4) -> bool:
        """
        Verifica se o usuário já enfrentou outro humano real nas últimas N partidas.
        Permite garantir a regra de negócio: 'obrigatoriamente ter um ser humano em alguma rodada'.
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
