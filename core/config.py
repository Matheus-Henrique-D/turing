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

# Temas Oficiais por Rodada (Icebreakers de Conversa)
ROUND_TOPICS = [
    "🍕 Comidas Polêmicas: Qual prato popular todo mundo ama mas você não suporta?",
    "🎬 Cinema & Séries: Qual filme aclamado você achou chato ou superestimado?",
    "🧟 Dilema Apocalíptico: Qual seria seu plano se um apocalipse zumbi começasse hoje?",
    "💸 Mega da Virada: Qual a primeira coisa bizarra que você compraria se ficasse milionário?",
    "🕹️ Nostalgia & Jogos: Qual jogo ou desenho animado mais marcou a sua infância?",
    "📱 Tecnologia & Vida: Você preferiria viver sem internet por 1 ano ou sem comida gostosa?",
    "🎒 Perrengues Reais: Qual foi o maior mico ou situação vergonhosa que você já passou?",
    "🎵 Gosto Musical: Qual música inusitada você escuta escondido no fone de ouvido?",
    "🚀 Teorias Malucas: Você acredita que já estamos sendo visitados por extraterrestres?",
    "💼 Rotina & Sonhos: Se você não precisasse de dinheiro, com o que gastaria seu tempo?"
]

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
