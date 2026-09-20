"""
core/config.py
Configurações globais da plataforma Turing (Human or Not?).
Centraliza parâmetros do sistema, regras de negócio e constantes de segurança.
"""

from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Banco de dados SQLite
DATABASE_PATH = DATA_DIR / "turing_platform.db"

# Regras de Negócio do Jogo
MAX_TURNS_PER_GAME = 5
OPPONENT_TYPES = ["HUMAN", "AI"]

# Perfis de Acesso (RBAC)
ROLE_USUARIO = "usuario"
ROLE_OPERADOR = "operador"
ROLE_ADMIN = "admin"
ALL_ROLES = [ROLE_USUARIO, ROLE_OPERADOR, ROLE_ADMIN]

# Status de Sessão de Jogo
STATUS_ACTIVE = "active"
STATUS_WAITING_OPERATOR = "waiting_operator"
STATUS_OPERATOR_ACTIVE = "operator_active"
STATUS_VOTING = "voting"
STATUS_FINISHED = "finished"

# Segurança
PASSWORD_SALT_BYTES = 16
PASSWORD_HASH_ITERATIONS = 100_000
MIN_PASSWORD_LENGTH = 6

# Chave secreta de sessão (para tokens ou sessões locais)
SECRET_KEY = "turing-secret-key-development-safe"
