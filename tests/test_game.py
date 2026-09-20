"""
tests/test_game.py
Testes unitários para a mecânica de 5 turnos, limites e votação do Teste de Turing.
"""

import unittest
from core.database import init_db
from services.auth_service import AuthService
from services.game_service import GameService
from core.config import STATUS_ACTIVE, STATUS_VOTING, STATUS_FINISHED

class TestGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.game_service = GameService()
        cls.user, _ = AuthService.authenticate("jogador1", "jogador123")

    def test_full_game_lifecycle_5_turns_and_vote(self):
        session = self.game_service.start_new_game(self.user.id)
        self.assertIsNotNone(session)
        self.assertEqual(session.status, STATUS_ACTIVE)

        # Envia 4 mensagens normais
        for i in range(1, 5):
            reply, status = self.game_service.send_user_message(
                session.id, self.user.username, f"Pergunta número {i}"
            )
            self.assertIsNotNone(reply)
            self.assertEqual(status, STATUS_ACTIVE)

        # 5ª mensagem -> deve transicionar para VOTING
        reply, status = self.game_service.send_user_message(
            session.id, self.user.username, "5ª e última pergunta"
        )
        self.assertEqual(status, STATUS_VOTING)

        # Votação
        is_win, actual, _ = self.game_service.submit_vote(session.id, "AI")
        final_session = self.game_service.get_session(session.id)
        self.assertEqual(final_session.status, STATUS_FINISHED)
        self.assertIn(final_session.opponent_type, ["HUMAN", "AI"])
        self.assertEqual(final_session.user_guess, "AI")

if __name__ == "__main__":
    unittest.main()
