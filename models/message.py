"""
models/message.py
Entidade Message e operações de persistência no SQLite.
"""

from dataclasses import dataclass
from datetime import datetime
from core.database import get_db_connection

@dataclass
class Message:
    id: int
    session_id: str
    sender_type: str  # 'user', 'ai', 'simulated_human', 'operator', 'system'
    sender_name: str
    content: str
    created_at: str

    @classmethod
    def from_row(cls, row) -> "Message":
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            sender_type=row["sender_type"],
            sender_name=row["sender_name"],
            content=row["content"],
            created_at=row["created_at"]
        )

class MessageRepository:
    @staticmethod
    def create(session_id: str, sender_type: str, sender_name: str, content: str) -> Message:
        now = datetime.now().isoformat()
        with get_db_connection() as conn:
            cursor = conn.execute("""
            INSERT INTO messages (session_id, sender_type, sender_name, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (session_id, sender_type, sender_name, content.strip(), now))
            msg_id = cursor.lastrowid
            
            cursor = conn.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
            return Message.from_row(cursor.fetchone())

    @staticmethod
    def list_by_session(session_id: str) -> list[Message]:
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """, (session_id,))
            return [Message.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def count_user_messages(session_id: str) -> int:
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT COUNT(*) as total
            FROM messages
            WHERE session_id = ? AND sender_type = 'user'
            """, (session_id,))
            row = cursor.fetchone()
            return row["total"] if row else 0
