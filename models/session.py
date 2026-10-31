"""
models/session.py
Entidade GameSession e repositório de partidas do Teste de Turing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid
from core.database import get_db_connection
from core.config import (
    STATUS_ACTIVE,
    STATUS_WAITING_OPERATOR,
    STATUS_OPERATOR_ACTIVE,
    STATUS_VOTING,
    STATUS_FINISHED
)

@dataclass
class GameSession:
    id: str
    user_id: int
    opponent_type: str
    persona: str
    status: str
    operator_id: Optional[int]
    user_guess: Optional[str]
    is_win: Optional[bool]
    created_at: str
    finished_at: Optional[str]
    topic: Optional[str] = None
    player2_id: Optional[int] = None
    player2_guess: Optional[str] = None
    player2_is_win: Optional[bool] = None
    is_multiplayer: bool = False
    pretend_ai_user_id: Optional[int] = None
    next_session_id: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "GameSession":
        keys = row.keys()
        topic_val = row["topic"] if "topic" in keys else None
        p2_id = row["player2_id"] if "player2_id" in keys else None
        p2_guess = row["player2_guess"] if "player2_guess" in keys else None
        p2_win = bool(row["player2_is_win"]) if "player2_is_win" in keys and row["player2_is_win"] is not None else None
        is_mp = bool(row["is_multiplayer"]) if "is_multiplayer" in keys and row["is_multiplayer"] is not None else False
        pretend_id = row["pretend_ai_user_id"] if "pretend_ai_user_id" in keys else None
        next_sid = row["next_session_id"] if "next_session_id" in keys else None

        return cls(
            id=row["id"],
            user_id=row["user_id"],
            opponent_type=row["opponent_type"],
            persona=row["persona"],
            status=row["status"],
            operator_id=row["operator_id"],
            user_guess=row["user_guess"],
            is_win=bool(row["is_win"]) if row["is_win"] is not None else None,
            created_at=row["created_at"],
            finished_at=row["finished_at"],
            topic=topic_val,
            player2_id=p2_id,
            player2_guess=p2_guess,
            player2_is_win=p2_win,
            is_multiplayer=is_mp,
            pretend_ai_user_id=pretend_id,
            next_session_id=next_sid
        )

class SessionRepository:
    @staticmethod
    def create(
        user_id: int,
        opponent_type: str,
        persona: str,
        topic: Optional[str] = None,
        player2_id: Optional[int] = None,
        is_multiplayer: bool = False,
        pretend_ai_user_id: Optional[int] = None
    ) -> GameSession:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with get_db_connection() as conn:
            conn.execute("""
            INSERT INTO game_sessions (id, user_id, opponent_type, persona, topic, status, created_at, player2_id, is_multiplayer, pretend_ai_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, opponent_type, persona, topic, STATUS_ACTIVE, now, player2_id, 1 if is_multiplayer else 0, pretend_ai_user_id))
        return SessionRepository.get_by_id(session_id)

    @staticmethod
    def get_by_id(session_id: str) -> Optional[GameSession]:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM game_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            return GameSession.from_row(row) if row else None

    @staticmethod
    def list_by_user(user_id: int, limit: int = 50) -> list[GameSession]:
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT * FROM game_sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """, (user_id, limit))
            return [GameSession.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def list_waiting_operator() -> list[dict]:
        """Retorna as sessões que solicitaram atendimento humano (fila de espera)."""
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT gs.*, u.username as player_username, u.full_name as player_full_name
            FROM game_sessions gs
            JOIN users u ON gs.user_id = u.id
            WHERE gs.status IN (?, ?)
            ORDER BY gs.created_at ASC
            """, (STATUS_WAITING_OPERATOR, STATUS_OPERATOR_ACTIVE))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def update_status(session_id: str, new_status: str, operator_id: Optional[int] = None) -> bool:
        with get_db_connection() as conn:
            if operator_id is not None:
                cursor = conn.execute("""
                UPDATE game_sessions
                SET status = ?, operator_id = ?
                WHERE id = ?
                """, (new_status, operator_id, session_id))
            else:
                cursor = conn.execute("""
                UPDATE game_sessions
                SET status = ?
                WHERE id = ?
                """, (new_status, session_id))
            return cursor.rowcount > 0

    @staticmethod
    def record_vote(session_id: str, user_guess: str, is_win: bool, user_id: Optional[int] = None) -> bool:
        now = datetime.now().isoformat()
        session = SessionRepository.get_by_id(session_id)
        if not session:
            return False

        with get_db_connection() as conn:
            if session.is_multiplayer and user_id is not None:
                if user_id == session.player2_id:
                    conn.execute("""
                    UPDATE game_sessions
                    SET player2_guess = ?, player2_is_win = ?
                    WHERE id = ?
                    """, (user_guess, 1 if is_win else 0, session_id))
                else:
                    conn.execute("""
                    UPDATE game_sessions
                    SET user_guess = ?, is_win = ?
                    WHERE id = ?
                    """, (user_guess, 1 if is_win else 0, session_id))

                # Se ambos já votaram, finaliza a sessão
                updated = SessionRepository.get_by_id(session_id)
                if updated and updated.user_guess is not None and updated.player2_guess is not None:
                    conn.execute("""
                    UPDATE game_sessions
                    SET status = ?, finished_at = ?
                    WHERE id = ?
                    """, (STATUS_FINISHED, now, session_id))
                return True
            else:
                cursor = conn.execute("""
                UPDATE game_sessions
                SET status = ?, user_guess = ?, is_win = ?, finished_at = ?
                WHERE id = ?
                """, (STATUS_FINISHED, user_guess, 1 if is_win else 0, now, session_id))
                return cursor.rowcount > 0

    @staticmethod
    def set_next_session(session_id: str, next_session_id: str) -> bool:
        """Salva o ID da próxima sessão (rodada seguinte) compartilhada entre os 2 jogadores."""
        with get_db_connection() as conn:
            cursor = conn.execute("""
            UPDATE game_sessions
            SET next_session_id = ?
            WHERE id = ?
            """, (next_session_id, session_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_stats_for_user(user_id: int) -> dict:
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE
                    WHEN user_id = ? AND is_win = 1 THEN 1
                    WHEN player2_id = ? AND player2_is_win = 1 THEN 1
                    ELSE 0
                END) as wins
            FROM game_sessions
            WHERE (user_id = ? OR player2_id = ?)
              AND (status = ? OR user_guess IS NOT NULL OR player2_guess IS NOT NULL)
            """, (user_id, user_id, user_id, user_id, STATUS_FINISHED))
            row = cursor.fetchone()
            total = row["total_games"] or 0
            wins = row["wins"] or 0
            win_rate = (wins / total * 100) if total > 0 else 0
            return {"total_games": total, "wins": wins, "win_rate": win_rate}

    @staticmethod
    def get_global_stats() -> dict:
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as total_wins,
                SUM(CASE WHEN opponent_type = 'AI' AND is_win = 1 THEN 1 ELSE 0 END) as ai_detected,
                SUM(CASE WHEN opponent_type = 'HUMAN' AND is_win = 1 THEN 1 ELSE 0 END) as human_detected,
                SUM(CASE WHEN status IN (?, ?) THEN 1 ELSE 0 END) as total_handoffs
            FROM game_sessions
            """, (STATUS_WAITING_OPERATOR, STATUS_OPERATOR_ACTIVE))
            row = cursor.fetchone()
            total = row["total_games"] or 0
            wins = row["total_wins"] or 0
            return {
                "total_games": total,
                "total_wins": wins,
                "win_rate": (wins / total * 100) if total > 0 else 0,
                "ai_detected": row["ai_detected"] or 0,
                "human_detected": row["human_detected"] or 0,
                "total_handoffs": row["total_handoffs"] or 0
            }
