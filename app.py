"""
app.py
Interface Web do Minijogo Teste de Turing (estilo HumanOrNot.so) construída com Streamlit.
"""

import streamlit as st
import time
import random
from bot_engine import TuringOpponent

# Configurações da Página
st.set_page_config(
    page_title="Turing Test: Human or Not?",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada (estilo HumanOrNot)
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #888888;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .badge-counter {
        background-color: #2b2d42;
        color: #edf2f4;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        font-size: 0.9rem;
    }
    .vote-box {
        background-color: #1e1e2f;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-top: 20px;
        border: 1px solid #3d3d5c;
    }
    .result-card-win {
        background: linear-gradient(135deg, #1d4ed8, #059669);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .result-card-loss {
        background: linear-gradient(135deg, #b91c1c, #d97706);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# Limite de mensagens por rodada
MAX_MESSAGES = 5

# Inicialização do Estado da Sessão
if "stats" not in st.session_state:
    st.session_state.stats = {"games": 0, "wins": 0}

def start_new_game():
    st.session_state.opponent = TuringOpponent()
    st.session_state.messages = []
    st.session_state.game_phase = "chat"  # 'chat', 'voting', 'result'
    st.session_state.user_vote = None
    st.session_state.interlocutor_typing = False

if "opponent" not in st.session_state:
    start_new_game()

# --- BARRA LATERAL (INFORMAÇÕES E ESTATÍSTICAS) ---
with st.sidebar:
    st.title("🎮 Teste de Turing")
    st.write("Inspirado no jogo **humanornot.so**.")
    st.info(
        "**Como Funciona:**\n"
        "1. Converse com o interlocutor misterioso.\n"
        "2. Você tem **5 mensagens** no total.\n"
        "3. Ao final, vote se você estava falando com um **Humano** ou uma **IA**."
    )
    
    st.markdown("---")
    st.subheader("📊 Seu Desempenho")
    col1, col2 = st.columns(2)
    col1.metric("Partidas", st.session_state.stats["games"])
    win_rate = (
        (st.session_state.stats["wins"] / st.session_state.stats["games"] * 100)
        if st.session_state.stats["games"] > 0 else 0
    )
    col2.metric("Acertos", f"{st.session_state.stats['wins']} ({win_rate:.0f}%)")
    
    st.markdown("---")
    with st.expander("💡 Ideias de perguntas do Teste de Turing"):
        st.write("""
        - *Qual é o próximo número da série: 3, 6, 9, 12, 15?*
        - *O que é 2×78?*
        - *Qual é a raiz quadrada de 2?*
        - *Você gosta de dançar ou jogar videogame?*
        - *Que dia é hoje e que horas são?*
        - *O que você acha de inteligência artificial?*
        """)

    if st.button("🔄 Reiniciar Partida", use_container_width=True):
        start_new_game()
        st.rerun()

# --- CABEÇALHO PRINCIPAL ---
st.markdown('<div class="main-title">Human or Not? 🤖 vs 👤</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Você consegue identificar quem está do outro lado?</div>', unsafe_allow_html=True)

# Contador de mensagens restantes
user_msg_count = sum(1 for m in st.session_state.messages if m["role"] == "user")
progress_val = min(user_msg_count / MAX_MESSAGES, 1.0)

col_prog, col_badge = st.columns([3, 1])
with col_prog:
    st.progress(progress_val)
with col_badge:
    st.markdown(f'<div class="badge-counter">Turno {user_msg_count}/{MAX_MESSAGES}</div>', unsafe_allow_html=True)

st.write("")

# --- RENDERIZAÇÃO DO HISTÓRICO DE CHAT ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="❓"):
            st.markdown(msg["content"])

# --- FASE 1: CHAT ATIVO ---
if st.session_state.game_phase == "chat":
    if user_msg_count < MAX_MESSAGES:
        user_input = st.chat_input("Digite sua mensagem para o interlocutor misterioso...")
        if user_input:
            # 1. Registra mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # 2. Resposta do oponente
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(user_input)
                
            with st.chat_message("assistant", avatar="❓"):
                with st.spinner("Interlocutor está digitando..."):
                    # Simula tempo de resposta humano/computacional
                    delay = random.uniform(1.2, 2.5) if st.session_state.opponent.opponent_type == "HUMAN" else random.uniform(0.6, 1.4)
                    time.sleep(delay)
                    
                    bot_reply = st.session_state.opponent.get_response(user_input)
                    st.markdown(bot_reply)
                    
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
            # Se atingiu o limite de 5 interações, muda para a fase de votação
            if sum(1 for m in st.session_state.messages if m["role"] == "user") >= MAX_MESSAGES:
                st.session_state.game_phase = "voting"
                
            st.rerun()
    else:
        st.session_state.game_phase = "voting"
        st.rerun()

# --- FASE 2: VOTAÇÃO ---
if st.session_state.game_phase == "voting":
    st.markdown("---")
    st.markdown("""
    <div class="vote-box">
        <h3>🛑 Fim da conversa!</h3>
        <p>Você atingiu o limite de 5 mensagens. Com base nas respostas, quem era seu interlocutor?</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    col_ai, col_human = st.columns(2)
    
    with col_ai:
        if st.button("🤖 Inteligência Artificial", use_container_width=True, type="primary"):
            st.session_state.user_vote = "AI"
            st.session_state.game_phase = "result"
            st.session_state.stats["games"] += 1
            if st.session_state.opponent.opponent_type == "AI":
                st.session_state.stats["wins"] += 1
            st.rerun()
            
    with col_human:
        if st.button("👤 Humano", use_container_width=True, type="primary"):
            st.session_state.user_vote = "HUMAN"
            st.session_state.game_phase = "result"
            st.session_state.stats["games"] += 1
            if st.session_state.opponent.opponent_type == "HUMAN":
                st.session_state.stats["wins"] += 1
            st.rerun()

# --- FASE 3: REVELAÇÃO DO RESULTADO ---
if st.session_state.game_phase == "result":
    actual = st.session_state.opponent.opponent_type
    voted = st.session_state.user_vote
    is_correct = (actual == voted)
    
    actual_label = "🤖 Inteligência Artificial" if actual == "AI" else "👤 Humano"
    voted_label = "🤖 Inteligência Artificial" if voted == "AI" else "👤 Humano"
    
    if is_correct:
        st.markdown(f"""
        <div class="result-card-win">
            <h2>🎉 PARABÉNS! VOCÊ ACERTOU!</h2>
            <p style="font-size: 1.2rem; margin-top: 10px;">
                Seu palpite: <b>{voted_label}</b><br>
                A verdade: Na verdade era <b>{actual_label}</b>!
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="result-card-loss">
            <h2>❌ VOCÊ FOI ENGANADO!</h2>
            <p style="font-size: 1.2rem; margin-top: 10px;">
                Seu palpite: <b>{voted_label}</b><br>
                A verdade: Na verdade era <b>{actual_label}</b>!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    if st.button("🎮 Jogar Outra Rodada", use_container_width=True, type="secondary"):
        start_new_game()
        st.rerun()
