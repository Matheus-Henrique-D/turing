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

HUMAN_PERSONAS = ["gamer_jovem", "estudante_neutro", "ironico_zoeiro", "casual_gente_boa"]
AI_PERSONAS = [
    "assistente_formal",
    "ia_tentando_disfarcar",
    "filosofica_precisa",
    "ia_camuflada",
    "ia_filosofica_sutil",
    "ia_ironica"
]

class GameService:
    def __init__(self, ai_provider = None):
        self.ai_provider = ai_provider or get_ai_provider()

    def start_new_game(self, user_id: int, exclude_topics: Optional[list] = None) -> GameSession:
        """Inicia uma nova partida de Teste de Turing para o usuário autenticado."""
        opponent_type = random.choice(["HUMAN", "AI"])
        if opponent_type == "HUMAN":
            persona = random.choice(HUMAN_PERSONAS)
        else:
            persona = random.choice(AI_PERSONAS)

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
