"""
models/user.py
Entidade User e operações de repositório no banco de dados SQLite.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from core.database import get_db_connection

@dataclass
class User:
    id: int
    username: str
    full_name: str
    password_hash: str
    salt: str
    role: str
    is_active: bool
    created_at: str

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"]
        )

class UserRepository:
    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
            row = cursor.fetchone()
            return User.from_row(row) if row else None

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return User.from_row(row) if row else None

    @staticmethod
    def create(username: str, full_name: str, password_hash: str, salt: str, role: str) -> User:
        now = datetime.now().isoformat()
        with get_db_connection() as conn:
            cursor = conn.execute("""
            INSERT INTO users (username, full_name, password_hash, salt, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (username.strip(), full_name.strip(), password_hash, salt, role, now))
            user_id = cursor.lastrowid
        return UserRepository.get_by_id(user_id)

    @staticmethod
    def list_all() -> list[User]:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [User.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def update_role(user_id: int, new_role: str) -> bool:
        with get_db_connection() as conn:
            cursor = conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
            return cursor.rowcount > 0

    @staticmethod
    def toggle_active(user_id: int, is_active: bool) -> bool:
        with get_db_connection() as conn:
            cursor = conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
            return cursor.rowcount > 0
