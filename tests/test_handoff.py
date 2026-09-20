"""
tests/test_handoff.py
Testes unitários para o fluxo de Handoff (solicitação, fila e intervenção do operador).
"""

import unittest
from core.database import init_db
from services.auth_service import AuthService
from services.game_service import GameService
from services.handoff_service import HandoffService
from core.config import STATUS_WAITING_OPERATOR, STATUS_OPERATOR_ACTIVE, STATUS_VOTING

class TestHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.game_service = GameService()
        cls.player, _ = AuthService.authenticate("jogador1", "jogador123")
        cls.operator, _ = AuthService.authenticate("operador", "operador123")

    def test_handoff_workflow(self):
        # 1. Jogador cria jogo
        session = self.game_service.start_new_game(self.player.id)
        
        # 2. Jogador solicita falar com humano
        ok, msg = HandoffService.request_human_handoff(session.id, self.player.id)
        self.assertTrue(ok)
        
        s_waiting = self.game_service.get_session(session.id)
        self.assertEqual(s_waiting.status, STATUS_WAITING_OPERATOR)

        # 3. Operador consulta fila e assume a conversa
        queue = HandoffService.get_pending_queue()
        session_ids = [q["id"] for q in queue]
        self.assertIn(session.id, session_ids)

        ok_assign, _ = HandoffService.assign_operator_to_session(session.id, self.operator)
        self.assertTrue(ok_assign)

        s_active = self.game_service.get_session(session.id)
        self.assertEqual(s_active.status, STATUS_OPERATOR_ACTIVE)
        self.assertEqual(s_active.operator_id, self.operator.id)

        # 4. Operador envia mensagem
        ok_msg, _ = HandoffService.send_operator_message(session.id, self.operator, "Olá, sou o operador!")
        self.assertTrue(ok_msg)

        # 5. Operador finaliza atendimento
        ok_fin, _ = HandoffService.finish_session_by_operator(session.id, self.operator, send_to_vote=True)
        self.assertTrue(ok_fin)

        s_final = self.game_service.get_session(session.id)
        self.assertEqual(s_final.status, STATUS_VOTING)

if __name__ == "__main__":
    unittest.main()
