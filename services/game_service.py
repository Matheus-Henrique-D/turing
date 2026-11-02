"""
services/game_service.py
Regras de negócio do Teste de Turing (minijogo de 5 turnos), persistência de histórico e votação.
"""

import random
from typing import Optional, Tuple
from core.config import (
    MAX_TURNS_PER_GAME,
    STATUS_ACTIVE,
    STATUS_VOTING,
    STATUS_FINISHED,
    STATUS_WAITING_OPERATOR,
    STATUS_OPERATOR_ACTIVE,
    ROUND_TOPICS
)
from models.session import GameSession, SessionRepository
from models.message import Message, MessageRepository
from services.ai_provider import get_ai_provider

# Personas de IA com comportamento mais robótico, analítico ou formal
ROBOTIC_AI_PERSONAS = [
    "assistente_formal",
    "filosofica_precisa",
    "ia_tentando_disfarcar"
]

# Personas de IA com comportamento altamente adaptativo (reagem e se adaptam diretamente ao player)
ADAPTIVE_HUMAN_PERSONAS = [
    "gamer_jovem",
    "estudante_neutro",
    "ironico_zoeiro",
    "casual_gente_boa",
    "ia_camuflada",
    "ia_adaptativa"
]

HUMAN_PERSONAS = ADAPTIVE_HUMAN_PERSONAS
AI_PERSONAS = ROBOTIC_AI_PERSONAS + ["ia_filosofica_sutil", "ia_ironica"]

class GameService:
    def __init__(self, ai_provider = None):
        self.ai_provider = ai_provider or get_ai_provider()

    def start_new_game(
        self,
        user_id: int,
        exclude_topics: Optional[list] = None,
        round_number: Optional[int] = None
    ) -> GameSession:
        """
        Inicia uma nova partida de Teste de Turing para o usuário autenticado.
        Garante a regra: em algumas rodadas a IA se comporta como robô, mas
        em pelo menos uma das rodadas ela se adapta diretamente ao que o player diz!
        """
        opponent_type = "AI"

        # Identifica a rodada atual do ciclo (1 a 3)
        current_round = round_number or (len(exclude_topics or []) + 1)

        # Seleciona estilo da persona de acordo com a rodada para garantir contraste:
        # Pelo menos uma rodada será puramente robótica/analítica e pelo menos uma será adaptativa
        if current_round == 1:
            # 50% de chance de começar robótica ou adaptativa
            pool = ROBOTIC_AI_PERSONAS if random.random() < 0.5 else ADAPTIVE_HUMAN_PERSONAS
        elif current_round == 2:
            # Rodada 2: alta probabilidade de alternar com a anterior
            pool = ADAPTIVE_HUMAN_PERSONAS if (current_round % 2 == 0) else ROBOTIC_AI_PERSONAS
        else:
            # Rodada 3: garante uma persona altamente adaptativa e espontânea
            pool = ADAPTIVE_HUMAN_PERSONAS

        persona = random.choice(pool)

        # Seleciona tema que não esteja na lista de exclusão
        available_topics = [t for t in ROUND_TOPICS if t not in (exclude_topics or [])]
        if not available_topics:
            available_topics = ROUND_TOPICS
        topic = random.choice(available_topics)

        session = SessionRepository.create(
            user_id=user_id,
            opponent_type=opponent_type,
            persona=persona,
            topic=topic
        )
        return session

    def get_or_create_next_multiplayer_round(self, previous_session: GameSession, exclude_topics: Optional[list] = None) -> GameSession:
        """
        Garante que a próxima rodada da mesma dupla multijogador seja criada de forma única.
        Se o parceiro já criou a próxima sessão, retorna ela. Caso contrário, cria e vincula.
        """
        import uuid
        from datetime import datetime
        from core.database import get_db_connection

        available_topics = [t for t in ROUND_TOPICS if t not in (exclude_topics or [])]
        if not available_topics:
            available_topics = ROUND_TOPICS
        topic = random.choice(available_topics)

        p_ids = [previous_session.user_id]
        if previous_session.player2_id:
            p_ids.append(previous_session.player2_id)
        pretend_id = random.choice(p_ids)

        # Verificação + criação + vínculo numa única transação com lock de escrita.
        # Antes, os dois aparelhos podiam criar uma sessão cada (corrida), e cada
        # jogador ficava esperando o ACK numa sessão diferente: um avançava, o outro não.
        new_id = None
        with get_db_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT next_session_id FROM game_sessions WHERE id = ?",
                (previous_session.id,)).fetchone()
            if row and row["next_session_id"]:
                new_id = row["next_session_id"]
            else:
                new_id = str(uuid.uuid4())
                conn.execute("""
                INSERT INTO game_sessions
                    (id, user_id, opponent_type, persona, topic, status, created_at,
                     player2_id, is_multiplayer, pretend_ai_user_id,
                     round_ready_ack, round_migrated_ack)
                VALUES (?, ?, 'HUMAN', 'jogador_real', ?, ?, ?, ?, 1, ?, 0, 0)
                """, (new_id, previous_session.user_id, topic, STATUS_ACTIVE,
                      datetime.now().isoformat(), previous_session.player2_id, pretend_id))
                conn.execute(
                    "UPDATE game_sessions SET next_session_id = ? WHERE id = ?",
                    (new_id, previous_session.id))
        return SessionRepository.get_by_id(new_id)

    def confirm_round_ready(self, next_session_id: str, user_id: int) -> dict:
        """
        Handshake de transição entre rodadas multiplayer.
        Atualiza round_ready_ack ATOMICAMENTE no SQL via bitwise OR.
        Retorna {'all_ready': bool, 'ready_count': int}.
        O fluxo só avança quando all_ready=True (ambos confirmaram).
        """
        from core.database import get_db_connection
        with get_db_connection() as conn:
            sess_cur = conn.execute(
                "SELECT user_id, player2_id FROM game_sessions WHERE id = ?", (next_session_id,))
            sess_row = sess_cur.fetchone()
            if not sess_row:
                return {"all_ready": False, "ready_count": 0}

            bit = 1 if user_id == sess_row["user_id"] else (2 if user_id == sess_row["player2_id"] else 0)
            if bit == 0:
                return {"all_ready": False, "ready_count": 0}

            # UPDATE atômico via SQL bitwise OR: nenhuma concorrência pode sobrescrever
            conn.execute(
                "UPDATE game_sessions SET round_ready_ack = (round_ready_ack | ?) WHERE id = ?",
                (bit, next_session_id)
            )

            check_cur = conn.execute(
                "SELECT round_ready_ack FROM game_sessions WHERE id = ?", (next_session_id,))
            check_row = check_cur.fetchone()
            current_ack = check_row["round_ready_ack"] if check_row else 0

        all_ready = (current_ack & 3) == 3
        ready_count = bin(current_ack & 3).count("1")
        return {"all_ready": all_ready, "ready_count": ready_count}

    def check_round_ready(self, next_session_id: str) -> dict:
        """Consulta o estado atual do handshake da próxima rodada sem modificar."""
        from core.database import get_db_connection
        with get_db_connection() as conn:
            check_cur = conn.execute(
                "SELECT round_ready_ack FROM game_sessions WHERE id = ?", (next_session_id,))
            check_row = check_cur.fetchone()
            current_ack = check_row["round_ready_ack"] if check_row else 0

        all_ready = (current_ack & 3) == 3
        ready_count = bin(current_ack & 3).count("1")
        return {"all_ready": all_ready, "ready_count": ready_count}

    def confirm_round_migrated(self, next_session_id: str, user_id: int):
        """Registra que este jogador já entrou na nova rodada, garantindo retenção de estado."""
        from core.database import get_db_connection
        with get_db_connection() as conn:
            sess_cur = conn.execute(
                "SELECT user_id, player2_id FROM game_sessions WHERE id = ?", (next_session_id,))
            sess_row = sess_cur.fetchone()
            if not sess_row:
                return
            bit = 1 if user_id == sess_row["user_id"] else (2 if user_id == sess_row["player2_id"] else 0)
            if bit:
                conn.execute(
                    "UPDATE game_sessions SET round_migrated_ack = (round_migrated_ack | ?) WHERE id = ?",
                    (bit, next_session_id)
                )

    def prepare_next_round_after_both_ready(self, previous_session_id: str, user_id: int,
                                            exclude_topics: Optional[list] = None) -> dict:
        """Hold each player at the finished round; create the next session only after both ACKs."""
        import uuid
        from datetime import datetime
        from core.database import get_db_connection

        with get_db_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            old = conn.execute(
                "SELECT user_id, player2_id, next_session_id, round_ready_ack FROM game_sessions WHERE id = ?",
                (previous_session_id,)).fetchone()
            if not old or not old["player2_id"]:
                return {"all_ready": False, "session_id": None}
            bit = 1 if user_id == old["user_id"] else (2 if user_id == old["player2_id"] else 0)
            if not bit:
                return {"all_ready": False, "session_id": None}
            conn.execute("UPDATE game_sessions SET round_ready_ack = (round_ready_ack | ?) WHERE id = ?",
                         (bit, previous_session_id))
            mask = conn.execute("SELECT round_ready_ack FROM game_sessions WHERE id = ?",
                                 (previous_session_id,)).fetchone()["round_ready_ack"] & 3
            if mask != 3:
                return {"all_ready": False, "session_id": None}

            next_id = old["next_session_id"]
            if not next_id:
                topics = [t for t in ROUND_TOPICS if t not in (exclude_topics or [])] or ROUND_TOPICS
                next_id = str(uuid.uuid4())
                topic = random.choice(topics)
                pretend_id = random.choice([old["user_id"], old["player2_id"]])
                conn.execute("""INSERT INTO game_sessions
                    (id, user_id, opponent_type, persona, topic, status, created_at,
                     player2_id, is_multiplayer, pretend_ai_user_id, round_ready_ack, round_migrated_ack)
                    VALUES (?, ?, 'HUMAN', 'jogador_real', ?, ?, ?, ?, 1, ?, 0, 0)""",
                    (next_id, old["user_id"], topic, STATUS_ACTIVE, datetime.now().isoformat(),
                     old["player2_id"], pretend_id))
                conn.execute("UPDATE game_sessions SET next_session_id = ? WHERE id = ?",
                             (next_id, previous_session_id))
            return {"all_ready": True, "session_id": next_id}

    def get_session(self, session_id: str) -> Optional[GameSession]:
        return SessionRepository.get_by_id(session_id)

    def get_messages(self, session_id: str) -> list[Message]:
        return MessageRepository.list_by_session(session_id)

    def send_user_message(self, session_id: str, username: str, content: str) -> Tuple[Optional[str], str]:
        """
        Registra a mensagem do usuário e gera a resposta do interlocutor misterioso.
        Retorna (resposta_interlocutor, novo_status).
        """
        session = SessionRepository.get_by_id(session_id)
        if not session:
            return None, "Sessão não encontrada."

        if session.status not in [STATUS_ACTIVE, STATUS_OPERATOR_ACTIVE]:
            return None, f"O jogo não está em fase de chat (status: {session.status})."

        # 1. Registra mensagem do usuário
        MessageRepository.create(
            session_id=session_id,
            sender_type="user",
            sender_name=username,
            content=content
        )

        all_msgs = MessageRepository.list_by_session(session_id)
        user_msgs = [m for m in all_msgs if m.sender_name == username]
        user_turn_count = len(user_msgs)

        # Se for partida MULTIJOGADOR REAL (Humano vs Humano em computadores diferentes)
        if session.is_multiplayer:
            # Em multijogador, não há geração de IA. A resposta virá do outro jogador.
            # Verifica se o limite de turnos foi atingido
            # (quando o jogador ou o total de trocas atingir o limite estipulado)
            if len(all_msgs) >= (MAX_TURNS_PER_GAME * 2):
                SessionRepository.update_status(session_id, STATUS_VOTING)
                return None, STATUS_VOTING
            return None, STATUS_ACTIVE

        # Se um operador humano assumiu a sessão (Handoff)
        if session.status == STATUS_OPERATOR_ACTIVE:
            # Não gera resposta automática; o operador responderá pelo painel
            return None, STATUS_OPERATOR_ACTIVE

        # 2. Resposta do interlocutor misterioso IA (com tema da rodada e persona)
        history_payload = [{"role": m.sender_type, "content": m.content} for m in all_msgs]
        
        reply_text = self.ai_provider.generate_response(
            user_message=content,
            chat_history=history_payload,
            opponent_type=session.opponent_type,
            persona=session.persona,
            topic=session.topic
        )

        sender_tag = "simulated_human" if session.opponent_type == "HUMAN" else "ai"
        MessageRepository.create(
            session_id=session_id,
            sender_type=sender_tag,
            sender_name="Interlocutor",
            content=reply_text
        )

        # 3. Verificação do limite de turnos (partida singleplayer)
        if user_turn_count >= MAX_TURNS_PER_GAME:
            SessionRepository.update_status(session_id, STATUS_VOTING)
            return reply_text, STATUS_VOTING

        return reply_text, STATUS_ACTIVE

    def submit_vote(self, session_id: str, user_guess: str, user_id: Optional[int] = None) -> Tuple[bool, str, str]:
        """
        Processa o voto do usuário ('AI' ou 'HUMAN').
        Retorna (is_win, actual_opponent, mensagem).
        """
        session = SessionRepository.get_by_id(session_id)
        if not session:
            return False, "", "Sessão inválida."

        if user_guess not in ["AI", "HUMAN"]:
            return False, "", "Opção de voto inválida."

        actual = session.opponent_type
        is_win = (actual == user_guess)
        SessionRepository.record_vote(session_id, user_guess, is_win, user_id=user_id)

        return is_win, actual, "Voto computado com sucesso."

    def get_user_statistics(self, user_id: int) -> dict:
        return SessionRepository.get_stats_for_user(user_id)
