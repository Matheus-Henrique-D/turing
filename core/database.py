"""
core/database.py
Gerenciamento de conexões SQLite, esquema relacional, migrações e seeds iniciais.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager
from core.config import (
    DATABASE_PATH,
    ROLE_ADMIN,
    ROLE_OPERADOR,
    ROLE_USUARIO
)
from core.security import generate_salt, hash_password

@contextmanager
def get_db_connection():
    """Gerenciador de contexto para conexão SQLite thread-safe."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Cria todas as tabelas necessárias e inicializa dados padrão (seed)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Tabela de Usuários
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('usuario', 'operador', 'admin')),
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """)
        
        # Tabela de Sessões de Jogo (Partidas do Teste de Turing)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            opponent_type TEXT NOT NULL CHECK(opponent_type IN ('HUMAN', 'AI')),
            persona TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active', 'waiting_operator', 'operator_active', 'voting', 'finished')),
            operator_id INTEGER NULL,
            user_guess TEXT NULL CHECK(user_guess IN ('HUMAN', 'AI', NULL)),
            is_win INTEGER NULL,
            created_at TEXT NOT NULL,
            finished_at TEXT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (operator_id) REFERENCES users (id)
        );
        """)
        
        # Tabela de Mensagens
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            sender_type TEXT NOT NULL CHECK(sender_type IN ('user', 'ai', 'simulated_human', 'operator', 'system')),
            sender_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES game_sessions (id) ON DELETE CASCADE
        );
        """)
        
        # Tabela de Logs de Auditoria
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """)
        
        # Criação de índices para performance em consultas de sessão e fila
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON game_sessions(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON game_sessions(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);")
        
        # Seed inicial de usuários para permitir login imediato
        seed_default_users(cursor)

def seed_default_users(cursor):
    """Cria usuários pré-configurados caso o banco esteja novo."""
    default_users = [
        ("admin", "Administrador do Sistema", "admin123", ROLE_ADMIN),
        ("operador", "Operador de Atendimento", "operador123", ROLE_OPERADOR),
        ("jogador1", "Jogador Teste", "jogador123", ROLE_USUARIO)
    ]
    
    now = datetime.now().isoformat()
    for username, full_name, password, role in default_users:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            salt = generate_salt()
            pwd_hash = hash_password(password, salt)
            cursor.execute("""
            INSERT INTO users (username, full_name, password_hash, salt, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (username, full_name, pwd_hash, salt, role, now))

def log_audit_event(user_id: int | None, action: str, details: str):
    """Registra uma ação no log de auditoria do sistema."""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        conn.execute("""
        INSERT INTO audit_logs (user_id, action, details, created_at)
        VALUES (?, ?, ?, ?)
        """, (user_id, action, details, now))
