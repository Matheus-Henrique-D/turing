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

    @classmethod
    def from_row(cls, row) -> "GameSession":
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
            finished_at=row["finished_at"]
        )

class SessionRepository:
    @staticmethod
    def create(user_id: int, opponent_type: str, persona: str) -> GameSession:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with get_db_connection() as conn:
            conn.execute("""
            INSERT INTO game_sessions (id, user_id, opponent_type, persona, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, opponent_type, persona, STATUS_ACTIVE, now))
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
    def record_vote(session_id: str, user_guess: str, is_win: bool) -> bool:
        now = datetime.now().isoformat()
        with get_db_connection() as conn:
            cursor = conn.execute("""
            UPDATE game_sessions
            SET status = ?, user_guess = ?, is_win = ?, finished_at = ?
            WHERE id = ?
            """, (STATUS_FINISHED, user_guess, 1 if is_win else 0, now, session_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_stats_for_user(user_id: int) -> dict:
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as wins
            FROM game_sessions
            WHERE user_id = ? AND status = ?
            """, (user_id, STATUS_FINISHED))
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
