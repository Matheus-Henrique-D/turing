"""
app.py
Plataforma "Human or Not?" (Teste de Turing Corporativo com RBAC, Handoff e Persistência).
Suporta perfis de Jogador (usuario), Operador de Atendimento e Administrador.
"""

import streamlit as st
import time
import random
from datetime import datetime

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
    STATUS_FINISHED
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
    page_title="Human or Not? — Plataforma Teste de Turing",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização visual moderna
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .badge-role {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    .badge-admin { background-color: #7c3aed; color: white; }
    .badge-operador { background-color: #2563eb; color: white; }
    .badge-usuario { background-color: #059669; color: white; }
    
    .card-session {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .vote-panel {
        background-color: #1e1e2f;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin-top: 15px;
        border: 1px solid #3d3d5c;
    }
    .result-win {
        background: linear-gradient(135deg, #1e40af, #047857);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .result-loss {
        background: linear-gradient(135deg, #991b1b, #d97706);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Instância de serviços
game_service = GameService()

# Inicialização do estado de sessão do Streamlit
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "operator_selected_session" not in st.session_state:
    st.session_state.operator_selected_session = None

# ==============================================================================
# TELA DE AUTENTICAÇÃO (LOGIN / REGISTRO)
# ==============================================================================
def render_auth_page():
    st.markdown("<h1 style='text-align:center;'>🤖 Human or Not? — Teste de Turing 👤</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>Plataforma Educacional e Experimental com Controle de Perfis (RBAC)</p>", unsafe_allow_html=True)
    
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        tab_login, tab_register = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

        with tab_login:
            st.subheader("Login no Sistema")
            login_user = st.text_input("Nome de Usuário", key="login_username")
            login_pass = st.text_input("Senha", type="password", key="login_password")
            
            if st.button("Acessar Plataforma", type="primary", use_container_width=True):
                user, err = AuthService.authenticate(login_user, login_pass)
                if user:
                    st.session_state.current_user = user
                    st.session_state.active_session_id = None
                    st.success(f"Bem-vindo, {user.full_name}!")
                    st.rerun()
                else:
                    st.error(err)

            st.markdown("---")
            with st.expander("👤 Contas de demonstração pré-configuradas"):
                st.markdown("""
                - **Administrador:** `admin` | Senha: `admin123`
                - **Operador de Atendimento:** `operador` | Senha: `operador123`
                - **Jogador / Usuário:** `jogador1` | Senha: `jogador123`
                """)

        with tab_register:
            st.subheader("Novo Cadastro")
            reg_name = st.text_input("Nome Completo", key="reg_name")
            reg_user = st.text_input("Nome de Usuário (login)", key="reg_user")
            reg_pass = st.text_input("Senha (mínimo 6 caracteres)", type="password", key="reg_pass")
            reg_confirm = st.text_input("Confirmar Senha", type="password", key="reg_confirm")

            if st.button("Cadastrar", type="primary", use_container_width=True):
                new_user, err = AuthService.register(reg_user, reg_name, reg_pass, reg_confirm)
                if new_user:
                    st.session_state.current_user = new_user
                    st.success("Cadastro realizado com sucesso!")
                    st.rerun()
                else:
                    st.error(err)

# Se não estiver logado, exibe apenas a tela de autenticação
if not st.session_state.current_user:
    render_auth_page()
    st.stop()

# ==============================================================================
# MENU LATERAL E CABEÇALHO DO USUÁRIO LOGADO
# ==============================================================================
user: User = st.session_state.current_user
role_class = f"badge-{user.role}"

with st.sidebar:
    st.markdown(f"### Olá, **{user.full_name}**")
    st.markdown(f"Perfil: <span class='badge-role {role_class}'>{user.role}</span>", unsafe_allow_html=True)
    st.write(f"Usuário: `{user.username}`")
    
    if st.button("🚪 Sair (Logout)", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.active_session_id = None
        st.rerun()

    st.markdown("---")
    
    # Navegação conforme o perfil RBAC
    allowed_views = ["🎮 Jogar (Teste de Turing)"]
    if user.role in [ROLE_OPERADOR, ROLE_ADMIN]:
        allowed_views.append("🎧 Painel do Operador (Handoff)")
    if user.role == ROLE_ADMIN:
        allowed_views.append("⚙️ Painel de Administração")

    selected_view = st.radio("Selecione a visualização:", allowed_views)

    st.markdown("---")
    st.caption("🧠 **Status da Inteligência Artificial:**")
    st.success("🟢 **Ollama Local Ativo**\nModelo: `llama3.2:1b` (100% Gratuito)")

# ==============================================================================
# VISÃO 1: JOGADOR (TESTE DE TURING & CHAT DE 5 TURNOS)
# ==============================================================================
if selected_view == "🎮 Jogar (Teste de Turing)":
    st.markdown("<div class='main-header'>Human or Not? 🤖 vs 👤</div>", unsafe_allow_html=True)
    st.caption("Você tem 5 mensagens para descobrir se está falando com um Humano ou com uma IA.")

    # Se não houver partida ativa, cria ou recupera
    if not st.session_state.active_session_id:
        if st.button("🎲 Iniciar Nova Partida", type="primary"):
            new_session = game_service.start_new_game(user.id)
            st.session_state.active_session_id = new_session.id
            st.rerun()
        else:
            # Mostra estatísticas do jogador
            stats = game_service.get_user_statistics(user.id)
            st.markdown("---")
            st.subheader("📊 Seu Histórico de Partidas")
            col1, col2, col3 = st.columns(3)
            col1.metric("Partidas Jogadas", stats["total_games"])
            col2.metric("Vitórias", stats["wins"])
            col3.metric("Taxa de Acerto", f"{stats['win_rate']:.1f}%")
            st.stop()

    current_session = game_service.get_session(st.session_state.active_session_id)
    if not current_session:
        st.session_state.active_session_id = None
        st.rerun()

    # Contador de turnos do usuário
    user_msgs = [m for m in game_service.get_messages(current_session.id) if m.sender_type == "user"]
    turn_count = len(user_msgs)
    progress_ratio = min(turn_count / MAX_TURNS_PER_GAME, 1.0)

    col_bar, col_tag, col_hand = st.columns([3, 1, 1])
    with col_bar:
        st.progress(progress_ratio)
    with col_tag:
        st.markdown(f"**Turno:** `{turn_count} / {MAX_TURNS_PER_GAME}`")
    with col_hand:
        if current_session.status == STATUS_ACTIVE:
            if st.button("🙋 Falar com Humano", help="Solicitar atendimento com um operador humano real"):
                HandoffService.request_human_handoff(current_session.id, user.id)
                st.rerun()

    # Mensagens de alerta sobre o status do atendimento humano
    if current_session.status == STATUS_WAITING_OPERATOR:
        st.warning("⏳ **Aguardando operador:** Sua solicitação de handoff está na fila de atendimento.")
    elif current_session.status == STATUS_OPERATOR_ACTIVE:
        st.info("🟢 **Atendimento Humano Ativo:** Você está em contato com um operador real.")

    # Renderiza mensagens do chat
    messages = game_service.get_messages(current_session.id)
    for m in messages:
        if m.sender_type == "user":
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(f"**Você:** {m.content}")
        elif m.sender_type == "operator":
            with st.chat_message("assistant", avatar="🎧"):
                st.markdown(f"**Operador ({m.sender_name}):** {m.content}")
        elif m.sender_type == "system":
            st.caption(f"ℹ️ *{m.content}*")
        else:
            with st.chat_message("assistant", avatar="❓"):
                st.markdown(f"**Interlocutor:** {m.content}")

    # Fluxo 1: Conversa ativa
    if current_session.status in [STATUS_ACTIVE, STATUS_OPERATOR_ACTIVE]:
        if turn_count < MAX_TURNS_PER_GAME:
            user_input = st.chat_input("Digite sua mensagem para o interlocutor...")
            if user_input:
                with st.spinner("Interlocutor está digitando..."):
                    reply, next_status = game_service.send_user_message(
                        current_session.id,
                        user.username,
                        user_input
                    )
                st.rerun()
        else:
            # Atingiu 5 turnos -> vai para votação
            st.rerun()

    # Fluxo 2: Votação
    elif current_session.status == STATUS_VOTING:
        st.markdown("---")
        st.markdown("""
        <div class="vote-panel">
            <h3>🛑 Conversa Encerrada!</h3>
            <p>Você completou 5 trocas de mensagens. Com quem você acredita que estava conversando?</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("🤖 É uma Inteligência Artificial", use_container_width=True, type="primary"):
                game_service.submit_vote(current_session.id, "AI")
                st.rerun()
        with col_v2:
            if st.button("👤 É um Humano", use_container_width=True, type="primary"):
                game_service.submit_vote(current_session.id, "HUMAN")
                st.rerun()

    # Fluxo 3: Resultado final
    elif current_session.status == STATUS_FINISHED:
        actual = current_session.opponent_type
        voted = current_session.user_guess
        is_win = current_session.is_win

        actual_str = "🤖 Inteligência Artificial" if actual == "AI" else "👤 Humano"
        voted_str = "🤖 Inteligência Artificial" if voted == "AI" else "👤 Humano"

        st.markdown("---")
        if is_win:
            st.markdown(f"""
            <div class="result-win">
                <h2>🎉 PARABÉNS! VOCÊ ACERTOU!</h2>
                <p>Seu voto: <b>{voted_str}</b> | A verdade: <b>{actual_str}</b></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="result-loss">
                <h2>❌ VOCÊ FOI ENGANADO!</h2>
                <p>Seu voto: <b>{voted_str}</b> | A verdade: <b>{actual_str}</b></p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        if st.button("🎲 Jogar Outra Rodada", use_container_width=True, type="primary"):
            st.session_state.active_session_id = None
            st.rerun()

# ==============================================================================
# VISÃO 2: PAINEL DO OPERADOR (FILA DE HANDOFF E ATENDIMENTO AO VIVO)
# ==============================================================================
elif selected_view == "🎧 Painel do Operador (Handoff)":
    st.markdown("<div class='main-header'>🎧 Painel de Atendimento do Operador</div>", unsafe_allow_html=True)
    st.caption("Gerenciamento de solicitações de handoff humano e intervenção direta no chat.")

    col_queue, col_chat = st.columns([1, 2])

    with col_queue:
        st.subheader("📋 Fila de Atendimento")
        queue = HandoffService.get_pending_queue()
        
        if not queue:
            st.info("Nenhuma conversa aguardando operador no momento.")
        else:
            for item in queue:
                status_icon = "⏳ Aguardando" if item["status"] == STATUS_WAITING_OPERATOR else "🟢 Em Atendimento"
                st.markdown(f"""
                <div class="card-session">
                    <b>Jogador:</b> {item['player_full_name']} (@{item['player_username']})<br>
                    <small>Status: {status_icon} | ID: {item['id'][:8]}...</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Abrir Chat ({item['player_username']})", key=f"btn_open_{item['id']}"):
                    st.session_state.operator_selected_session = item["id"]
                    st.rerun()

    with col_chat:
        st.subheader("💬 Atendimento ao Vivo")
        sel_id = st.session_state.operator_selected_session
        
        if not sel_id:
            st.write("Selecione uma conversa na fila ao lado para iniciar o atendimento.")
        else:
            session = game_service.get_session(sel_id)
            if not session:
                st.warning("Sessão não encontrada.")
            else:
                # Ações do operador
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    if session.status == STATUS_WAITING_OPERATOR:
                        if st.button("🙋 Assumir Conversa", type="primary", use_container_width=True):
                            HandoffService.assign_operator_to_session(session.id, user)
                            st.rerun()
                with col_act2:
                    if session.status == STATUS_OPERATOR_ACTIVE:
                        if st.button("✅ Finalizar Atendimento", use_container_width=True):
                            HandoffService.finish_session_by_operator(session.id, user, send_to_vote=True)
                            st.rerun()

                st.markdown("---")
                # Histórico da conversa para o operador
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

                # Campo para o operador responder
                if session.status == STATUS_OPERATOR_ACTIVE:
                    st.markdown("---")
                    with st.form(key="operator_msg_form", clear_on_submit=True):
                        op_reply = st.text_input("Sua resposta para o jogador:")
                        send_btn = st.form_submit_button("Enviar Mensagem")
                        if send_btn and op_reply:
                            HandoffService.send_operator_message(session.id, user, op_reply)
                            st.rerun()

# ==============================================================================
# VISÃO 3: PAINEL DE ADMINISTRAÇÃO (RBAC, MÉTRICAS E LOGS)
# ==============================================================================
elif selected_view == "⚙️ Painel de Administração":
    st.markdown("<div class='main-header'>⚙️ Painel de Controle e Governança</div>", unsafe_allow_html=True)
    st.caption("Administração de usuários, controle de permissões (RBAC), métricas globais e trilha de auditoria.")

    tab_users, tab_metrics, tab_audit = st.tabs(["👥 Gestão de Usuários", "📈 Métricas do Sistema", "📜 Logs de Auditoria"])

    # Aba 1: Gestão de Usuários
    with tab_users:
        st.subheader("Usuários Registrados no Sistema")
        all_users = AdminService.list_all_users()

        for u in all_users:
            col_u1, col_u2, col_u3, col_u4 = st.columns([2, 1, 1, 1])
            with col_u1:
                status_symbol = "🟢 Ativo" if u.is_active else "🔴 Bloqueado"
                st.markdown(f"**{u.full_name}** (`{u.username}`)<br><small>{status_symbol} | Criado em: {u.created_at[:10]}</small>", unsafe_allow_html=True)
            with col_u2:
                new_role = st.selectbox(
                    "Perfil (Role)",
                    [ROLE_USUARIO, ROLE_OPERADOR, ROLE_ADMIN],
                    index=[ROLE_USUARIO, ROLE_OPERADOR, ROLE_ADMIN].index(u.role),
                    key=f"role_sel_{u.id}"
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
                    st.caption("(Conta própria)")
            with col_u4:
                st.write("")
            st.divider()

    # Aba 2: Métricas Consolidadas
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

    # Aba 3: Logs de Auditoria
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
                    "Detalhes": l["details"]
                }
                for l in logs
            ]
            st.dataframe(log_display, use_container_width=True)
