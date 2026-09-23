"""
app.py
Plataforma "Human or Not?" (Teste de Turing Corporativo com RBAC, Handoff e Persistência).
Suporta perfis de Jogador (usuario), Operador de Atendimento e Administrador.

DESIGN:
  Inspirado no visual retro-arcade / cyberpunk do "Human or Not?", com estética
  dark navy (#020b1e), verde neon terminal (#00ff44), magenta elétrico (#ff007f),
  bolhas retangulares nítidas, partículas digitais no rodapé e HUD futurista.
"""

import streamlit as st
import os
import time
import random
from datetime import datetime

# Timer por turno — usa st_autorefresh para forçar rerun periódico a cada 1s.
try:
    from streamlit_autorefresh import st_autorefresh  # type: ignore
    _HAS_AUTOREFRESH = True
except ImportError:
    _HAS_AUTOREFRESH = False

from core.database import init_db
from core.config import (
    MAX_TURNS_PER_GAME,
    ROLE_USUARIO,
    ROLE_OPERADOR,
    ROLE_ADMIN,
    STATUS_ACTIVE,
    STATUS_WAITING_OPERATOR,
    STATUS_OPERATOR_ACTIVE,
    STATUS_VOTING,
    STATUS_FINISHED,
)
from services.auth_service import AuthService
from services.game_service import GameService
from services.handoff_service import HandoffService
from services.admin_service import AdminService
from models.user import User

# Inicializa o banco de dados e sementes padrão
init_db()

# Configuração da página Streamlit
st.set_page_config(
    page_title="Human or Not? — Teste de Turing",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# CSS CENTRALIZADO COM VARIÁVEIS :root (TEMA RETRO-ARCADE / HUMAN OR NOT)
# ==============================================================================
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=VT323&display=swap');

  :root {
    --bg-dark:       #020b1e;
    --bg-mid:        #06132e;
    --bg-card:       #0b1d42;
    --ink:           #e2edfc;
    --muted:         #6b8bb8;
    --line:          #162a52;
    --neon-green:    #00ff55;
    --neon-green-dim:#00c844;
    --neon-glow:     rgba(0, 255, 85, 0.28);
    --neon-magenta:  #ff0080;
    --neon-magenta-glow: rgba(255, 0, 128, 0.25);
    --danger:        #ff3355;
    --danger-soft:   rgba(255, 51, 85, 0.15);
    --warn:          #ffbe1a;
    --font-mono:     'Share Tech Mono', monospace;
    --font-pixel:    'VT323', monospace;
  }

  /* ── Fundo global e tipografia ────────────────────────────── */
  .stApp,
  body,
  [data-testid="stAppViewContainer"],
  [data-testid="stHeader"] {
    background: var(--bg-dark) !important;
    font-family: var(--font-mono) !important;
    color: var(--ink) !important;
  }

  /* Efeito de grade sutil no fundo (digital grid) */
  [data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
      linear-gradient(to right, rgba(0, 255, 85, 0.02) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0, 255, 85, 0.02) 1px, transparent 1px);
    background-size: 32px 32px;
    z-index: 0;
  }

  /* Poeira de pixels digitais no rodapé (inspirado na imagem de referência) */
  [data-testid="stAppViewContainer"]::after {
    content: '';
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: 140px;
    pointer-events: none;
    background:
      radial-gradient(3px 3px at 4% 82%, var(--neon-green) 100%, transparent),
      radial-gradient(2px 2px at 9% 94%, var(--neon-green) 100%, transparent),
      radial-gradient(4px 4px at 15% 72%, var(--neon-green) 100%, transparent),
      radial-gradient(3px 3px at 22% 88%, var(--neon-green) 100%, transparent),
      radial-gradient(2px 2px at 29% 96%, var(--neon-magenta) 100%, transparent),
      radial-gradient(4px 4px at 36% 76%, var(--neon-green) 100%, transparent),
      radial-gradient(3px 3px at 44% 84%, var(--neon-green) 100%, transparent),
      radial-gradient(2px 2px at 52% 92%, var(--neon-green) 100%, transparent),
      radial-gradient(4px 4px at 59% 68%, var(--neon-magenta) 100%, transparent),
      radial-gradient(3px 3px at 67% 86%, var(--neon-green) 100%, transparent),
      radial-gradient(2px 2px at 74% 94%, var(--neon-green) 100%, transparent),
      radial-gradient(4px 4px at 82% 78%, var(--neon-green) 100%, transparent),
      radial-gradient(3px 3px at 89% 88%, var(--neon-green) 100%, transparent),
      radial-gradient(2px 2px at 95% 74%, var(--neon-magenta) 100%, transparent);
    opacity: 0.65;
    animation: digital-dust 6s ease-in-out infinite alternate;
    z-index: 0;
  }
  @keyframes digital-dust {
    0%   { transform: translateY(0); opacity: 0.65; }
    100% { transform: translateY(-12px); opacity: 0.35; }
  }

  /* ── Textos e cabeçalhos ──────────────────────────────────── */
  [data-testid="stMarkdownContainer"],
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] span,
  [data-testid="stMarkdownContainer"] li,
  [data-testid="stMarkdownContainer"] strong,
  h1, h2, h3, h4, h5, h6,
  .stText, label,
  [data-testid="stMetricLabel"],
  [data-testid="stMetricValue"],
  [data-testid="stMetricDelta"] {
    color: var(--ink) !important;
    font-family: var(--font-mono) !important;
  }

  .main-header {
    color: var(--neon-green) !important;
    font-family: var(--font-pixel), monospace !important;
    font-size: 2.8rem;
    letter-spacing: 0.08em;
    line-height: 1.1;
    text-shadow: 0 0 16px var(--neon-green), 0 0 32px rgba(0, 255, 85, 0.4);
    margin-bottom: 0.2rem;
  }

  .hud-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--bg-mid);
    border: 1px solid var(--neon-green-dim);
    padding: 4px 12px;
    border-radius: 2px;
    font-family: var(--font-pixel), monospace;
    font-size: 1.3rem;
    color: var(--neon-green);
    box-shadow: 0 0 10px rgba(0, 255, 85, 0.15);
  }

  /* ── Sidebar ──────────────────────────────────────────────── */
  [data-testid="stSidebar"] {
    background: var(--bg-mid) !important;
    border-right: 1px solid var(--line);
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.4);
  }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span {
    color: var(--ink) !important;
  }
  [data-testid="stSidebar"] hr, hr {
    border-color: var(--line) !important;
  }

  /* ── Layout Container ─────────────────────────────────────── */
  .block-container {
    max-width: 1040px;
    padding-top: 2rem;
    padding-bottom: 5rem;
    position: relative;
    z-index: 1;
  }

  /* ── Botões Arcade / Retro ────────────────────────────────── */
  .stButton > button,
  .stDownloadButton > button {
    background: var(--bg-card);
    border: 1px solid var(--neon-green-dim);
    border-radius: 2px;
    min-height: 2.5rem;
    font-family: var(--font-mono) !important;
    font-weight: 600;
    color: var(--neon-green) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    transition: all 120ms ease;
    box-shadow: 0 0 8px rgba(0, 255, 85, 0.1);
  }
  .stButton > button:hover,
  .stDownloadButton > button:hover {
    border-color: var(--neon-green);
    background: var(--neon-glow);
    color: #ffffff !important;
    box-shadow: 0 0 18px var(--neon-green);
    transform: translateY(-1px);
  }
  .stButton > button[kind="primary"] {
    background: var(--neon-green) !important;
    border-color: var(--neon-green) !important;
    color: #020b1e !important;
    font-weight: 800;
    box-shadow: 0 0 20px var(--neon-glow);
  }
  .stButton > button[kind="primary"]:hover {
    background: #00ff77 !important;
    box-shadow: 0 0 30px var(--neon-green);
  }

  /* ── Inputs e Caixas de Texto ─────────────────────────────── */
  input, textarea,
  [data-baseweb="select"] > div,
  [data-baseweb="input"] > div {
    background: var(--bg-card) !important;
    color: var(--neon-green) !important;
    border-color: var(--line) !important;
    border-radius: 2px !important;
    font-family: var(--font-mono) !important;
  }
  input:focus, textarea:focus,
  [data-baseweb="input"] > div:focus-within {
    border-color: var(--neon-green) !important;
    box-shadow: 0 0 12px var(--neon-glow) !important;
  }
  input::placeholder, textarea::placeholder {
    color: var(--muted) !important;
  }
  [data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--neon-green-dim) !important;
    border-radius: 2px !important;
    box-shadow: 0 0 14px rgba(0, 255, 85, 0.15) !important;
  }

  /* ── Bolhas de Chat (Inspirado exatamente nas imagens) ────── */
  .chat-stream {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;
  }

  .bubble-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    width: 100%;
  }
  .bubble-row.user-row {
    justify-content: flex-end;
  }
  .bubble-row.opponent-row {
    justify-content: flex-start;
  }

  /* Jogador: Caixa retangular VERDE NEON vibrante, texto escuro/preto */
  .bubble-box-user {
    background: var(--neon-green);
    color: #020b1e;
    padding: 14px 20px;
    border-radius: 2px;
    max-width: 65%;
    font-weight: 700;
    font-size: 1.02rem;
    line-height: 1.45;
    box-shadow: 0 0 18px rgba(0, 255, 85, 0.35);
    word-break: break-word;
  }

  /* Interlocutor: Caixa retangular BRANCA pura e nítida, texto escuro */
  .bubble-box-opponent {
    background: #ffffff;
    color: #020b1e;
    padding: 14px 20px;
    border-radius: 2px;
    max-width: 65%;
    font-weight: 600;
    font-size: 1.02rem;
    line-height: 1.45;
    box-shadow: 0 0 16px rgba(255, 255, 255, 0.2);
    word-break: break-word;
  }

  /* Avatar do Interlocutor: '?' em magenta neon pixelado (idêntico à ref) */
  .avatar-opponent-q {
    background: var(--bg-mid);
    border: 1px solid var(--neon-magenta);
    color: var(--neon-magenta);
    font-family: var(--font-pixel), monospace;
    font-size: 1.8rem;
    font-weight: bold;
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 2px;
    box-shadow: 0 0 12px var(--neon-magenta-glow);
    flex-shrink: 0;
  }

  /* Avatar do Jogador: ícone neon cyber */
  .avatar-user-badge {
    background: var(--bg-mid);
    border: 1px solid var(--neon-green);
    color: var(--neon-green);
    font-family: var(--font-pixel), monospace;
    font-size: 1.5rem;
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 2px;
    box-shadow: 0 0 12px var(--neon-glow);
    flex-shrink: 0;
  }

  /* Mensagem de sistema / log */
  .bubble-system {
    background: rgba(255, 190, 26, 0.1);
    border: 1px dashed var(--warn);
    color: var(--warn) !important;
    padding: 8px 16px;
    border-radius: 2px;
    font-size: 0.88rem;
    text-align: center;
    width: 100%;
  }

  /* ── Indicador "Digitando..." Pixelado ────────────────────── */
  .typing-box {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
  }
  .typing-pixels {
    display: flex;
    gap: 6px;
    padding: 14px 18px;
    background: var(--bg-card);
    border: 1px solid var(--neon-magenta);
    border-radius: 2px;
    box-shadow: 0 0 12px var(--neon-magenta-glow);
  }
  .typing-pixels span {
    width: 8px;
    height: 8px;
    background: var(--neon-magenta);
    border-radius: 1px;
    display: inline-block;
    animation: pixel-bounce 0.9s infinite ease-in-out;
  }
  .typing-pixels span:nth-child(2) { animation-delay: 0.2s; }
  .typing-pixels span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes pixel-bounce {
    0%, 100% { transform: translateY(0); opacity: 0.3; }
    50%      { transform: translateY(-6px); opacity: 1; box-shadow: 0 0 8px var(--neon-magenta); }
  }

  /* ── Timer HUD Digital (00:XX) ────────────────────────────── */
  .timer-hud {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-mid);
    border: 1px solid var(--line);
    padding: 8px 16px;
    border-radius: 2px;
    margin-bottom: 12px;
  }
  .timer-clock {
    font-family: var(--font-pixel), monospace;
    font-size: 1.8rem;
    letter-spacing: 0.05em;
    color: var(--neon-green);
    text-shadow: 0 0 10px var(--neon-green);
  }
  .timer-clock.urgent {
    color: var(--danger) !important;
    text-shadow: 0 0 12px var(--danger) !important;
    animation: urgent-pulse 0.7s infinite alternate;
  }
  @keyframes urgent-pulse {
    0%   { opacity: 1; }
    100% { opacity: 0.45; }
  }
  .timer-progress-track {
    flex-grow: 1;
    height: 6px;
    background: var(--line);
    margin: 0 16px;
    border-radius: 1px;
    overflow: hidden;
  }
  .timer-progress-fill {
    height: 100%;
    background: var(--neon-green);
    box-shadow: 0 0 8px var(--neon-green);
    transition: width 0.9s linear;
  }
  .timer-progress-fill.urgent {
    background: var(--danger) !important;
    box-shadow: 0 0 10px var(--danger) !important;
  }

  /* ── Cards de Votação e Resultados ────────────────────────── */
  .vote-panel {
    background: var(--bg-card);
    border: 1px solid var(--neon-green-dim);
    border-top: 3px solid var(--neon-green);
    border-radius: 2px;
    padding: 24px;
    margin-top: 20px;
    box-shadow: 0 0 20px rgba(0, 255, 85, 0.1);
  }
  .vote-panel h3 {
    color: var(--neon-green) !important;
    font-family: var(--font-pixel), monospace !important;
    font-size: 2.2rem;
    margin-bottom: 6px;
  }

  .result-win {
    background: rgba(0, 255, 85, 0.08);
    border: 2px solid var(--neon-green);
    border-radius: 2px;
    padding: 28px;
    text-align: center;
    box-shadow: 0 0 35px var(--neon-glow);
  }
  .result-win h2 {
    color: var(--neon-green) !important;
    font-family: var(--font-pixel), monospace !important;
    font-size: 2.6rem;
    text-shadow: 0 0 18px var(--neon-green);
  }

  .result-loss {
    background: var(--danger-soft);
    border: 2px solid var(--danger);
    border-radius: 2px;
    padding: 28px;
    text-align: center;
    box-shadow: 0 0 35px rgba(255, 51, 85, 0.25);
  }
  .result-loss h2 {
    color: var(--danger) !important;
    font-family: var(--font-pixel), monospace !important;
    font-size: 2.6rem;
    text-shadow: 0 0 18px var(--danger);
  }

  /* ── Badges de Role ───────────────────────────────────────── */
  .badge-role {
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.75rem;
    font-family: var(--font-mono) !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: inline-block;
  }
  .badge-admin    { background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #a855f7; }
  .badge-operador { background: var(--neon-glow); color: var(--neon-green); border: 1px solid var(--neon-green-dim); }
  .badge-usuario  { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }

  /* ── Card Operador ────────────────────────────────────────── */
  .card-session {
    background: var(--bg-card);
    border: 1px solid var(--line);
    border-left: 3px solid var(--neon-green);
    border-radius: 2px;
    padding: 14px;
    margin-bottom: 10px;
    transition: all 120ms ease;
  }
  .card-session:hover {
    border-color: var(--neon-green);
    box-shadow: 0 0 12px var(--neon-glow);
  }

  /* Métricas e tabelas */
  [data-testid="stMetricValue"] {
    color: var(--neon-green) !important;
    font-family: var(--font-pixel), monospace !important;
    font-size: 2rem !important;
  }
  [data-testid="stAlert"] {
    background: var(--bg-card) !important;
    border-radius: 2px !important;
    border-color: var(--line) !important;
  }
  [data-testid="stDataFrame"] {
    background: var(--bg-card);
    border: 1px solid var(--line);
  }
  [data-baseweb="tab-list"] {
    border-bottom: 1px solid var(--line) !important;
  }
  [data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 2px solid var(--neon-green) !important;
    color: var(--neon-green) !important;
  }
</style>
""", unsafe_allow_html=True)

# Instância de serviços
game_service = GameService()

# Inicialização de variáveis de sessão
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "operator_selected_session" not in st.session_state:
    st.session_state.operator_selected_session = None

# Timer por turno (mantido exclusivamente em memória na sessão, nunca no banco)
if "turn_start_time" not in st.session_state:
    st.session_state.turn_start_time = None
if "turn_index_at_start" not in st.session_state:
    st.session_state.turn_index_at_start = 0
if "turn_limit_seconds" not in st.session_state:
    st.session_state.turn_limit_seconds = 40
if "timer_expired_handled" not in st.session_state:
    st.session_state.timer_expired_handled = False


# ==============================================================================
# COMPONENTES VISUAIS HELPER
# ==============================================================================
def render_chat_bubble(content: str, role: str, label: str = "", avatar: str = ""):
    """Renderiza balões de mensagem estilizados conforme o design de referência."""
    if role == "system":
        st.markdown(
            f'<div class="bubble-system">ℹ️ {content}</div>',
            unsafe_allow_html=True,
        )
        return

    if role == "user":
        # Jogador à direita: caixa verde neon retangular + avatar cyber
        html = f"""
        <div class="bubble-row user-row">
            <div class="bubble-box-user">{content}</div>
            <div class="avatar-user-badge">👤</div>
        </div>
        """
    else:
        # Interlocutor à esquerda: avatar magenta "?" pixelado + caixa branca nítida
        html = f"""
        <div class="bubble-row opponent-row">
            <div class="avatar-opponent-q">?</div>
            <div class="bubble-box-opponent">{content}</div>
        </div>
        """
    st.markdown(html, unsafe_allow_html=True)


def render_typing_indicator():
    """Indicador animado com avatar pixelado e blocos em magenta."""
    st.markdown("""
    <div class="typing-box">
        <div class="avatar-opponent-q">?</div>
        <div class="typing-pixels">
            <span></span><span></span><span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_timer_hud(elapsed: float, limit: float):
    """
    Timer com contador em formato relógio digital '00:SS' e barra de progresso.
    Fica vermelho e pulsa nos últimos 10 segundos.
    """
    remaining = max(0.0, limit - elapsed)
    pct = (remaining / limit) * 100
    urgent = remaining <= 10
    urgent_cls = "urgent" if urgent else ""
    seconds_display = f"00:{int(remaining):02d}"

    st.markdown(f"""
    <div class="timer-hud">
        <span style="font-size:0.85rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.06em;">Tempo do Turno</span>
        <div class="timer-progress-track">
            <div class="timer-progress-fill {urgent_cls}" style="width:{pct:.1f}%;"></div>
        </div>
        <div class="timer-clock {urgent_cls}">⏱ {seconds_display}</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# TELA DE AUTENTICAÇÃO (LOGIN / REGISTRO)
# ==============================================================================
def render_auth_page():
    st.markdown("<div style='text-align:center; padding: 20px 0;'>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-header'>HUMAN OR NOT?</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:var(--muted); font-size:1.1rem;'>TESTE DE TURING EXPERIMENTAL // RBAC & PERSISTÊNCIA</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        tab_login, tab_register = st.tabs(["🔑 ENTRAR", "📝 NOVO CADASTRO"])

        with tab_login:
            st.write("")
            login_user = st.text_input("Usuário", key="login_username")
            login_pass = st.text_input("Senha", type="password", key="login_password")

            if st.button("ACESSAR PLATAFORMA", type="primary", use_container_width=True):
                user, err = AuthService.authenticate(login_user, login_pass)
                if user:
                    st.session_state.current_user = user
                    st.session_state.active_session_id = None
                    st.success(f"Conectado: {user.full_name}")
                    st.rerun()
                else:
                    st.error(err)

            st.markdown("---")
            with st.expander("👤 Contas de demonstração"):
                st.markdown("""
                - **Administrador:** `admin` | Senha: `admin123`
                - **Operador:** `operador` | Senha: `operador123`
                - **Jogador:** `jogador1` | Senha: `jogador123`
                """)

        with tab_register:
            st.write("")
            reg_name = st.text_input("Nome Completo", key="reg_name")
            reg_user = st.text_input("Nome de Usuário", key="reg_user")
            reg_pass = st.text_input("Senha (mínimo 6 caracteres)", type="password", key="reg_pass")
            reg_confirm = st.text_input("Confirmar Senha", type="password", key="reg_confirm")

            if st.button("CADASTRAR", type="primary", use_container_width=True):
                new_user, err = AuthService.register(reg_user, reg_name, reg_pass, reg_confirm)
                if new_user:
                    st.session_state.current_user = new_user
                    st.success("Conta criada com sucesso!")
                    st.rerun()
                else:
                    st.error(err)


# Se não autenticado, interrompe o fluxo na tela de login
current_user = st.session_state.get("current_user")
if not current_user:
    render_auth_page()
    st.stop()

# ==============================================================================
# MENU LATERAL (SIDEBAR)
# ==============================================================================
user: User = current_user
role_class = f"badge-{getattr(user, 'role', 'usuario')}"

with st.sidebar:
    st.markdown(f"### Olá, **{user.full_name}**")
    st.markdown(
        f"Perfil: <span class='badge-role {role_class}'>{user.role}</span>",
        unsafe_allow_html=True,
    )
    st.write(f"Identificador: `{user.username}`")

    if st.button("🚪 Sair (Logout)", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.active_session_id = None
        st.session_state.turn_start_time = None
        st.rerun()

    st.markdown("---")

    allowed_views = ["🎮 Jogar (Teste de Turing)"]
    if user.role in [ROLE_OPERADOR, ROLE_ADMIN]:
        allowed_views.append("🎧 Painel do Operador (Handoff)")
    if user.role == ROLE_ADMIN:
        allowed_views.append("⚙️ Painel de Administração")

    selected_view = st.radio("Módulo de visualização:", allowed_views)

    st.markdown("---")
    st.caption("🧠 **Provedor de Inteligência Artificial**")
    provider_name = os.getenv("TURING_AI_PROVIDER", "ollama").lower()
    provider_label = {
        "ollama": "Ollama Local (Llama 3.2)",
        "bert": "BERTimbau Base",
        "bertimbau": "BERTimbau Base",
        "mock": "Modo Heurístico Offline",
    }.get(provider_name, provider_name.title())
    st.info(f"**{provider_label}**\n\nMotor de inferência ativo")


# ==============================================================================
# VISÃO 1: JOGADOR (TESTE DE TURING // 5 TURNOS)
# ==============================================================================
if selected_view == "🎮 Jogar (Teste de Turing)":
    st.markdown("<div class='main-header'>HUMAN OR NOT?</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:var(--muted); margin-bottom: 20px;'>Descubra em 5 mensagens se você está conversando com um Humano ou com uma IA.</p>", unsafe_allow_html=True)

    # Iniciar partida caso não haja sessão ativa
    if not st.session_state.active_session_id:
        if st.button("🎲 INICIAR NOVA PARTIDA", type="primary", use_container_width=True):
            new_session = game_service.start_new_game(user.id)
            st.session_state.active_session_id = new_session.id
            st.session_state.turn_start_time = time.time()
            st.session_state.turn_index_at_start = 0
            st.session_state.timer_expired_handled = False
            # Limite por tipo de oponente: 40-50s para HUMAN, 30s para AI
            st.session_state.turn_limit_seconds = (
                random.randint(40, 50) if new_session.opponent_type == "HUMAN" else 30
            )
            st.rerun()
        else:
            stats = game_service.get_user_statistics(user.id)
            st.markdown("---")
            st.subheader("📊 Histórico do Jogador")
            col1, col2, col3 = st.columns(3)
            col1.metric("Partidas Jogadas", stats["total_games"])
            col2.metric("Vitórias", stats["wins"])
            col3.metric("Taxa de Acerto", f"{stats['win_rate']:.1f}%")
            st.stop()

    current_session = game_service.get_session(st.session_state.active_session_id)
    if not current_session:
        st.session_state.active_session_id = None
        st.rerun()

    # Contagem de turnos do jogador
    user_msgs = [m for m in game_service.get_messages(current_session.id) if m.sender_type == "user"]
    turn_count = len(user_msgs)
    progress_ratio = min(turn_count / MAX_TURNS_PER_GAME, 1.0)

    # Header da partida (Turnos + Botão de Handoff)
    col_bar, col_tag, col_hand = st.columns([3, 1, 1])
    with col_bar:
        st.progress(progress_ratio)
    with col_tag:
        st.markdown(f"<div class='hud-badge'>TURNO {turn_count}/{MAX_TURNS_PER_GAME}</div>", unsafe_allow_html=True)
    with col_hand:
        if current_session.status == STATUS_ACTIVE:
            if st.button("🙋 Falar com Humano", help="Solicitar atendimento com um operador humano real"):
                HandoffService.request_human_handoff(current_session.id, user.id)
                st.rerun()

    # Alertas de Handoff Humano
    if current_session.status == STATUS_WAITING_OPERATOR:
        st.warning("⏳ **Aguardando operador:** Conversa inserida na fila de atendimento.")
    elif current_session.status == STATUS_OPERATOR_ACTIVE:
        st.info("🟢 **Atendimento Humano Ativo:** Você está falando diretamente com um operador real.")

    st.write("")

    # Renderiza histórico do chat
    messages = game_service.get_messages(current_session.id)
    for m in messages:
        if m.sender_type == "user":
            render_chat_bubble(m.content, role="user")
        elif m.sender_type == "operator":
            render_chat_bubble(f"[Operador {m.sender_name}]: {m.content}", role="opponent")
        elif m.sender_type == "system":
            render_chat_bubble(m.content, role="system")
        else:
            render_chat_bubble(m.content, role="opponent")

    # ── 1. Conversa Ativa ──────────────────────────────────────────────────────
    if current_session.status in [STATUS_ACTIVE, STATUS_OPERATOR_ACTIVE]:
        if turn_count < MAX_TURNS_PER_GAME:

            # Reset do timer ao iniciar um novo turno
            if st.session_state.turn_index_at_start != turn_count:
                st.session_state.turn_start_time = time.time()
                st.session_state.turn_index_at_start = turn_count
                st.session_state.timer_expired_handled = False
                st.session_state.turn_limit_seconds = (
                    random.randint(40, 50)
                    if current_session.opponent_type == "HUMAN"
                    else 30
                )

            elapsed = time.time() - (st.session_state.turn_start_time or time.time())
            limit = st.session_state.turn_limit_seconds

            # Exibe HUD do timer durante chat ativo
            if current_session.status == STATUS_ACTIVE:
                render_timer_hud(elapsed, limit)

            # Expiração do timer: envia mensagem padrão "..." automaticamente
            # Decisão de design: enviar "..." reaproveita send_user_message com consistência.
            if (
                current_session.status == STATUS_ACTIVE
                and elapsed >= limit
                and not st.session_state.timer_expired_handled
            ):
                st.session_state.timer_expired_handled = True
                st.warning("⏰ Tempo esgotado! Turno enviado automaticamente.")
                typing_placeholder = st.empty()
                with typing_placeholder:
                    render_typing_indicator()

                reply, next_status = game_service.send_user_message(
                    current_session.id, user.username, "..."
                )
                if reply:
                    delay = len(reply) * 0.035 + random.uniform(0.3, 0.8)
                    time.sleep(min(delay, 3.0))

                typing_placeholder.empty()
                st.rerun()

            # Entrada de texto do jogador
            user_input = st.chat_input("Digite sua mensagem para o interlocutor...")
            if user_input:
                typing_placeholder = st.empty()
                with typing_placeholder:
                    render_typing_indicator()

                reply, next_status = game_service.send_user_message(
                    current_session.id,
                    user.username,
                    user_input,
                )

                # Delay de digitação proporcional ao tamanho da resposta gerada
                if reply:
                    delay = len(reply) * 0.035 + random.uniform(0.3, 0.8)
                    time.sleep(min(delay, 3.2))

                typing_placeholder.empty()
                st.rerun()

            # Rerun periódico para o timer regressivo
            if _HAS_AUTOREFRESH and current_session.status == STATUS_ACTIVE:
                st_autorefresh(interval=1000, key="chat_timer_refresh")

        else:
            # 5 turnos finalizados -> redireciona para a votação
            st.rerun()

    # ── 2. Votação ─────────────────────────────────────────────────────────────
    elif current_session.status == STATUS_VOTING:
        st.markdown("""
        <div class="vote-panel">
            <h3>🛑 CONVERSA FINALIZADA!</h3>
            <p style="font-size:1.05rem;">Você completou as 5 mensagens. Com quem você acredita que estava conversando?</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("🤖 É UMA INTELIGÊNCIA ARTIFICIAL", use_container_width=True, type="primary"):
                game_service.submit_vote(current_session.id, "AI")
                st.rerun()
        with col_v2:
            if st.button("👤 É UM HUMANO", use_container_width=True, type="primary"):
                game_service.submit_vote(current_session.id, "HUMAN")
                st.rerun()

    # ── 3. Resultado Final ─────────────────────────────────────────────────────
    elif current_session.status == STATUS_FINISHED:
        actual = current_session.opponent_type
        voted = current_session.user_guess
        is_win = current_session.is_win

        actual_str = "🤖 Inteligência Artificial" if actual == "AI" else "👤 Humano"
        voted_str = "🤖 Inteligência Artificial" if voted == "AI" else "👤 Humano"

        st.write("")
        if is_win:
            st.markdown(f"""
            <div class="result-win">
                <h2>🎉 PARABÉNS! VOCÊ ACERTOU!</h2>
                <p style="font-size:1.15rem; margin-top:10px;">
                    Seu voto: <b>{voted_str}</b> &nbsp;|&nbsp; A verdade: <b>{actual_str}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="result-loss">
                <h2>❌ VOCÊ FOI ENGANADO!</h2>
                <p style="font-size:1.15rem; margin-top:10px;">
                    Seu voto: <b>{voted_str}</b> &nbsp;|&nbsp; A verdade: <b>{actual_str}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        if st.button("🎲 JOGAR OUTRA RODADA", use_container_width=True, type="primary"):
            st.session_state.active_session_id = None
            st.session_state.turn_start_time = None
            st.session_state.timer_expired_handled = False
            st.rerun()


# ==============================================================================
# VISÃO 2: PAINEL DO OPERADOR (FILA DE HANDOFF)
# ==============================================================================
elif selected_view == "🎧 Painel do Operador (Handoff)":
    st.markdown("<div class='main-header'>PAINEL DO OPERADOR</div>", unsafe_allow_html=True)
    st.caption("Fila de solicitações de intervenção humana e atendimento em tempo real.")

    col_queue, col_chat = st.columns([1, 2])

    with col_queue:
        st.subheader("📋 Fila de Chamados")
        queue = HandoffService.get_pending_queue()

        if not queue:
            st.info("Nenhuma conversa aguardando operador no momento.")
        else:
            for item in queue:
                status_icon = (
                    "⏳ Aguardando"
                    if item["status"] == STATUS_WAITING_OPERATOR
                    else "🟢 Em Atendimento"
                )
                st.markdown(f"""
                <div class="card-session">
                    <b>Jogador:</b> {item['player_full_name']} (@{item['player_username']})<br>
                    <small>Status: {status_icon} | ID: {item['id'][:8]}...</small>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Atender @{item['player_username']}", key=f"btn_open_{item['id']}"):
                    st.session_state.operator_selected_session = item["id"]
                    st.rerun()

    with col_chat:
        st.subheader("💬 Sala de Atendimento")
        sel_id = st.session_state.operator_selected_session

        if not sel_id:
            st.write("Selecione um jogador na fila ao lado para iniciar a conversa.")
        else:
            session = game_service.get_session(sel_id)
            if not session:
                st.warning("Sessão não encontrada.")
            else:
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    if session.status == STATUS_WAITING_OPERATOR:
                        if st.button("🙋 Assumir Conversa", type="primary", use_container_width=True):
                            HandoffService.assign_operator_to_session(session.id, user)
                            st.rerun()
                with col_act2:
                    if session.status == STATUS_OPERATOR_ACTIVE:
                        if st.button("✅ Encerrar e Enviar para Voto", use_container_width=True):
                            HandoffService.finish_session_by_operator(session.id, user, send_to_vote=True)
                            st.rerun()

                st.markdown("---")
                msgs = game_service.get_messages(session.id)
                for m in msgs:
                    if m.sender_type == "user":
                        st.markdown(f"**🧑‍💻 Jogador:** {m.content}")
                    elif m.sender_type == "operator":
                        st.markdown(f"**🎧 Operador ({m.sender_name}):** {m.content}")
                    elif m.sender_type == "system":
                        st.caption(f"*{m.content}*")
                    else:
                        st.markdown(f"**🤖 Bot/IA:** {m.content}")

                if session.status == STATUS_OPERATOR_ACTIVE:
                    st.markdown("---")
                    with st.form(key="operator_msg_form", clear_on_submit=True):
                        op_reply = st.text_input("Sua resposta para o jogador:")
                        send_btn = st.form_submit_button("Enviar Mensagem")
                        if send_btn and op_reply:
                            HandoffService.send_operator_message(session.id, user, op_reply)
                            st.rerun()


# ==============================================================================
# VISÃO 3: PAINEL DE ADMINISTRAÇÃO (RBAC, MÉTRICAS E AUDITORIA)
# ==============================================================================
elif selected_view == "⚙️ Painel de Administração":
    st.markdown("<div class='main-header'>PAINEL DE GOVERNANÇA</div>", unsafe_allow_html=True)
    st.caption("Gestão de credenciais, controle de perfis (RBAC), métricas de detecção e trilha de auditoria.")

    tab_users, tab_metrics, tab_audit = st.tabs(
        ["👥 Gestão de Usuários", "📈 Métricas do Jogo", "📜 Auditoria & Logs"]
    )

    # ── Aba 1: Gestão de Usuários ──────────────────────────────────────────────
    with tab_users:
        st.subheader("Usuários Registrados no Sistema")

        search_query = st.text_input(
            "🔍 Filtrar usuários por nome ou username:",
            placeholder="Digite para filtrar instantaneamente...",
            key="admin_user_search",
        )
        all_users = AdminService.list_all_users()

        if search_query.strip():
            q = search_query.strip().lower()
            all_users = [
                u for u in all_users
                if q in u.username.lower() or q in u.full_name.lower()
            ]
            if not all_users:
                st.info(f"Nenhum usuário localizado para o termo '{search_query}'.")

        for u in all_users:
            col_u1, col_u2, col_u3, col_u4 = st.columns([2, 1, 1, 1])
            with col_u1:
                status_symbol = "🟢 Ativo" if u.is_active else "🔴 Bloqueado"
                st.markdown(
                    f"**{u.full_name}** (`{u.username}`)<br>"
                    f"<small>{status_symbol} | Criado em: {u.created_at[:10]}</small>",
                    unsafe_allow_html=True,
                )
            with col_u2:
                new_role = st.selectbox(
                    "Perfil (Role)",
                    [ROLE_USUARIO, ROLE_OPERADOR, ROLE_ADMIN],
                    index=[ROLE_USUARIO, ROLE_OPERADOR, ROLE_ADMIN].index(u.role),
                    key=f"role_sel_{u.id}",
                )
                if new_role != u.role:
                    ok, msg = AdminService.change_user_role(user, u.id, new_role)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col_u3:
                btn_label = "Bloquear" if u.is_active else "Ativar"
                btn_type = "secondary" if u.is_active else "primary"
                if u.id != user.id:
                    if st.button(btn_label, key=f"tog_{u.id}", type=btn_type):
                        ok, msg = AdminService.toggle_user_active(user, u.id, not u.is_active)
                        if ok:
                            st.info(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.caption("(Sua conta)")
            with col_u4:
                st.write("")
            st.divider()

    # ── Aba 2: Métricas ────────────────────────────────────────────────────────
    with tab_metrics:
        st.subheader("Indicadores Gerais de Desempenho")
        metrics = AdminService.get_dashboard_metrics()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Usuários", metrics["total_users"])
        m2.metric("Partidas Concluídas", metrics["total_games"])
        m3.metric("Vitórias Globais", f"{metrics['total_wins']} ({metrics['win_rate']:.1f}%)")
        m4.metric("Handoffs para Operador", metrics["total_handoffs"])

        st.markdown("---")
        st.subheader("Detecções do Teste de Turing")
        col_d1, col_d2 = st.columns(2)
        col_d1.metric("Acertos em Interlocutor IA", metrics["ai_detected"])
        col_d2.metric("Acertos em Interlocutor Humano", metrics["human_detected"])

    # ── Aba 3: Auditoria ───────────────────────────────────────────────────────
    with tab_audit:
        st.subheader("Trilha de Auditoria e Segurança")
        logs = AdminService.get_audit_logs(limit=50)

        if not logs:
            st.info("Nenhum evento registrado até o momento.")
        else:
            log_display = [
                {
                    "Data/Hora": l["created_at"][:19].replace("T", " "),
                    "Usuário": l["username"] or "Sistema",
                    "Ação": l["action"],
                    "Detalhes": l["details"],
                }
                for l in logs
            ]
            st.dataframe(log_display, use_container_width=True)
