"""
services/handoff_service.py
Serviço de Handoff (Transição para Atendimento Humano) e Painel do Operador.
"""

from typing import Optional, Tuple
from core.config import (
    STATUS_WAITING_OPERATOR,
    STATUS_OPERATOR_ACTIVE,
    STATUS_VOTING,
    STATUS_FINISHED
)
from models.session import SessionRepository, GameSession
from models.message import MessageRepository
from models.user import User
from core.database import log_audit_event

class HandoffService:
    @staticmethod
    def request_human_handoff(session_id: str, user_id: int) -> Tuple[bool, str]:
        """
        Solicita a transferência da conversa para um operador humano real.
        """
        session = SessionRepository.get_by_id(session_id)
        if not session:
            return False, "Sessão não encontrada."

        if session.status in [STATUS_WAITING_OPERATOR, STATUS_OPERATOR_ACTIVE]:
            return True, "A solicitação já está na fila de atendimento."

        # Atualiza status no banco de dados
        SessionRepository.update_status(session_id, STATUS_WAITING_OPERATOR)
        
        # Insere mensagem de sistema informativa no histórico
        MessageRepository.create(
            session_id=session_id,
            sender_type="system",
            sender_name="Sistema",
            content="[Aviso] Você solicitou falar com um atendente humano. Aguarde um operador conectar-se."
        )

        log_audit_event(user_id, "HANDOFF_REQUESTED", f"Usuário solicitou operador para a sessão {session_id}")
        return True, "Solicitação de operador realizada com sucesso."

    @staticmethod
    def get_pending_queue() -> list[dict]:
        """Retorna todas as conversas aguardando ou em atendimento por operadores."""
        return SessionRepository.list_waiting_operator()

    @staticmethod
    def assign_operator_to_session(session_id: str, operator: User) -> Tuple[bool, str]:
        """Atribui a conversa a um operador específico."""
        session = SessionRepository.get_by_id(session_id)
        if not session:
            return False, "Sessão não encontrada."

        SessionRepository.update_status(session_id, STATUS_OPERATOR_ACTIVE, operator_id=operator.id)
        
        MessageRepository.create(
            session_id=session_id,
            sender_type="system",
            sender_name="Sistema",
            content=f"[Aviso] O operador {operator.full_name} entrou na conversa."
        )

        log_audit_event(operator.id, "OPERATOR_ASSIGNED", f"Operador {operator.username} assumiu a sessão {session_id}")
        return True, "Sessão assumida com sucesso."

    @staticmethod
    def send_operator_message(session_id: str, operator: User, content: str) -> Tuple[bool, str]:
        """Envia mensagem escrita pelo operador para o usuário."""
        if not content.strip():
            return False, "A mensagem não pode estar vazia."

        MessageRepository.create(
            session_id=session_id,
            sender_type="operator",
            sender_name=operator.full_name,
            content=content.strip()
        )
        return True, "Mensagem enviada com sucesso."

    @staticmethod
    def finish_session_by_operator(session_id: str, operator: User, send_to_vote: bool = True) -> Tuple[bool, str]:
        """Conclui o atendimento do operador e direciona para votação ou encerramento."""
        new_status = STATUS_VOTING if send_to_vote else STATUS_FINISHED
        SessionRepository.update_status(session_id, new_status)
        
        MessageRepository.create(
            session_id=session_id,
            sender_type="system",
            sender_name="Sistema",
            content="[Aviso] O atendimento humano foi finalizado pelo operador."
        )

        log_audit_event(operator.id, "OPERATOR_FINISHED", f"Operador concluiu atendimento da sessão {session_id}")
        return True, "Atendimento finalizado com sucesso."
