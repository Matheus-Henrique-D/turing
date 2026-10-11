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
    # Comida & Cotidiano
    "🍕 Comidas Polêmicas: Qual prato popular todo mundo ama mas você não suporta?",
    "🍔 Fast Food Confissões: Qual combinação bizarra de comida você faz que todo mundo acha horrível?",
    "☕ Ritual Matinal: Você é do time café, suco ou pula o café da manhã de vez?",

    # Cinema & Séries
    "🎬 Cinema Decepcionante: Qual filme aclamado você achou chato ou superestimado?",
    "📺 Séries Viciantes: Qual série te fez perder noite de sono sem conseguir parar de assistir?",
    "🎞️ Final Injusto: Qual personagem de filme ou série morreu de forma mais absurda e desnecessária?",

    # Jogos (Games)
    "🕹️ Jogo de Infância: Qual jogo marcou tanto sua infância que você ainda lembra a trilha sonora?",
    "🎮 Mecânica Odiada: Qual mecânica de jogo você acha impossível de defender mas o jogo é popular?",
    "💀 Morte Humilhante: Qual foi a morte mais ridícula e constrangedora que você já sofreu num jogo?",
    "🏆 Gamer Confissão: Você já desistiu de um jogo próximo do final por pura raiva ou dificuldade?",

    # Animes
    "⚔️ Anime Favorito: Qual anime você recomendaria para alguém que nunca assistiu e por quê?",
    "😭 Anime que Destruiu: Qual cena ou personagem de anime te fez chorar (ou quase) sem querer?",
    "🔥 Debate Anime: Naruto ou Dragon Ball — qual teve a saga mais épica e por quê?",

    # Hobbies & Passatempos
    "🎨 Hobby Secreto: Qual hobbie ou passatempo você tem mas não conta pra quase ninguém?",
    "📸 Vício Inofensivo: Qual coisa inútil (mas divertida) você faz por horas sem perceber o tempo passar?",
    "🎲 Saudade de Brincar: Qual brincadeira da infância você voltaria a fazer hoje sem vergonha?",

    # Medos
    "😱 Medo Irracional: Qual coisa completamente irracional te apavora de um jeito que você sente vergonha de admitir?",
    "🕷️ Fobia Revelada: Baratas, palhaços ou altura — qual dos três te paralisa mais e por quê?",
    "🌙 Terror Noturno: Você já acordou no meio da madrugada com aquela sensação de que alguém estava no quarto?",

    # Sonhos & Ambições
    "🌟 Sonho Guardado: Qual sonho você ainda não perseguiu mas pensa nele de vez em quando?",
    "🚀 Vida Alternativa: Se pudesse recomeçar com outra profissão, o que escolheria sem pensar no dinheiro?",
    "🗺️ Lugar dos Sonhos: Qual lugar do mundo você mais quer visitar antes de morrer e o que faria lá?",

    # Frustrações
    "😤 Frustração Real: Qual coisa simples do dia a dia te irrita de um jeito desproporcional?",
    "📚 Arrependimento Escolar: Tem algo que você não aprendeu na escola e se arrepende até hoje?",
    "😩 Energia Desperdiçada: Qual fase da sua vida você acha que desperdiçou mais tempo?",

    # Livros & Leitura
    "📖 Livro Marcante: Qual livro (ou mangá) mudou sua forma de ver alguma coisa de verdade?",
    "📕 Leitura Difícil: Alguma vez você começou um livro famoso e desistiu no meio? Qual e por quê?",
    "✍️ Escritor por um Dia: Se você escrevesse um livro, qual seria o tema e quem seria o protagonista?",

    # Música
    "🎵 Playlist Secreta: Qual música você escuta escondido que nunca admitiria em público?",
    "🎤 Música na Alma: Qual letra de música te traz uma memória específica só de ouvir?",
    "🎸 Debate Musical: Você consegue ouvir música enquanto estuda/trabalha ou atrapalha totalmente?",

    # Dilemas & Reflexões
    "🧟 Apocalipse Zumbi: Qual seria seu plano de sobrevivência se o apocalipse zumbi começasse amanhã?",
    "💸 Milionário de Repente: Qual seria a primeira compra inútil e impulsiva que você faria?",
    "📱 Detox Digital: Você sobreviveria 1 semana sem celular? O que faria de diferente?",
    "🌍 Super Poder Inútil: Qual super poder completamente inútil você escolheria se fosse a única opção?",
    "🔮 Máquina do Tempo: Voltaria ao passado para mudar algo ou preferiria ir ao futuro?",
    "🧠 Pergunta Filosófica: Você acredita no livre-arbítrio ou acha que tudo já está de certa forma determinado?",
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
