import unittest
from core.database import init_db
from core.config import ROUND_TOPICS
from models.session import SessionRepository
from services.auth_service import AuthService
from services.game_service import GameService

class TestRound3AIRequirement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.game_service = GameService()
        u1, _ = AuthService.authenticate("jogador1", "jogador123")
        u2, _ = AuthService.authenticate("jogador2", "jogador123")
        cls.u1 = u1
        cls.u2 = u2

    def test_round3_multiplayer_transitions_both_to_ai_with_different_topics(self):
        # 1. Simula uma sessão multijogador da Rodada 2 finalizada
        round2_topic = ROUND_TOPICS[0]
        round2_session = SessionRepository.create(
            user_id=self.u1.id,
            opponent_type="HUMAN",
            persona="jogador_real",
            topic=round2_topic,
            player2_id=self.u2.id,
            is_multiplayer=True
        )

        # 2. Player 1 solicita a 3ª rodada
        sess_p1 = self.game_service.get_or_create_round3_ai_session(
            previous_session=round2_session,
            current_user_id=self.u1.id,
            exclude_topics=[round2_topic]
        )

        # 3. Player 2 solicita a 3ª rodada
        sess_p2 = self.game_service.get_or_create_round3_ai_session(
            previous_session=round2_session,
            current_user_id=self.u2.id,
            exclude_topics=[round2_topic]
        )

        # Asserções de conformidade estrita com o pedido do usuário:
        # a) Ambos enfrentam IA
        self.assertEqual(sess_p1.opponent_type, "AI", "Player 1 deve enfrentar a IA na rodada 3")
        self.assertEqual(sess_p2.opponent_type, "AI", "Player 2 deve enfrentar a IA na rodada 3")

        # b) Cada jogador tem sua própria sessão solo
        self.assertEqual(sess_p1.user_id, self.u1.id)
        self.assertEqual(sess_p2.user_id, self.u2.id)
        self.assertNotEqual(sess_p1.id, sess_p2.id)

        # c) Os temas da 3ª rodada são estritamente diferentes entre si
        self.assertNotEqual(sess_p1.topic, sess_p2.topic, "Os temas de P1 e P2 na rodada 3 devem ser diferentes!")

        # d) Nenhum dos dois repete o tema da rodada 2
        self.assertNotEqual(sess_p1.topic, round2_topic)
        self.assertNotEqual(sess_p2.topic, round2_topic)

        # e) Idempotência: chamadas subsequentes retornam a mesma sessão vinculada
        sess_p1_reconnected = self.game_service.get_or_create_round3_ai_session(
            previous_session=round2_session,
            current_user_id=self.u1.id
        )
        self.assertEqual(sess_p1.id, sess_p1_reconnected.id)

    def test_round1_and_round2_multiplayer_remain_unchanged(self):
        # Garante que as rodadas 1 e 2 entre players continuam HUMAN e compartilhadas
        s1 = SessionRepository.create(
            user_id=self.u1.id,
            opponent_type="HUMAN",
            persona="jogador_real",
            topic=ROUND_TOPICS[1],
            player2_id=self.u2.id,
            is_multiplayer=True
        )

        s2 = self.game_service.get_or_create_next_multiplayer_round(s1)
        self.assertEqual(s2.opponent_type, "HUMAN", "Rodadas 1 e 2 devem continuar sendo entre humanos")
        self.assertTrue(s2.is_multiplayer)
        self.assertEqual(s2.user_id, self.u1.id)
        self.assertEqual(s2.player2_id, self.u2.id)

if __name__ == "__main__":
    unittest.main()
