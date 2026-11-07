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

    def test_multiplayer_turn_order_and_message_counting(self):
        from models.session import SessionRepository
        from core.database import get_db_connection
        from core.security import generate_salt, hash_password
        import uuid
        from datetime import datetime

        # Cria os dois usuários se não existirem
        with get_db_connection() as conn:
            salt = generate_salt()
            pwd = hash_password("senha123", salt)
            for uid, uname in [(301, "tester_human"), (302, "pretend_bot")]:
                conn.execute("""
                INSERT OR IGNORE INTO users (id, username, full_name, password_hash, salt, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 'usuario', 1, '2026-01-01T00:00:00')
                """, (uid, uname, f"Nome {uname}", pwd, salt))

        sess_id = str(uuid.uuid4())
        # 301 é quem investiga, 302 é quem tem a missão de fingir ser IA
        with get_db_connection() as conn:
            conn.execute("""
            INSERT INTO game_sessions
                (id, user_id, opponent_type, persona, topic, status, created_at,
                 player2_id, is_multiplayer, pretend_ai_user_id)
            VALUES (?, 301, 'HUMAN', 'jogador_real', 'Tema Teste', 'active', ?, 302, 1, 302)
            """, (sess_id, datetime.now().isoformat()))

        # 1. Jogador 302 (missão de fingir de IA) tenta iniciar a rodada -> Deve ser bloqueado!
        reply, status = self.game_service.send_user_message(sess_id, "pretend_bot", "Olá, sou bot")
        self.assertIsNone(reply)
        self.assertEqual(status, "O jogador que não tem a missão de fingir ser IA deve iniciar a rodada.")

        # 2. Jogador 301 (sem a missão) inicia a rodada -> Deve ser aceito!
        reply, status = self.game_service.send_user_message(sess_id, "tester_human", "Oi! Você é humano?")
        self.assertIsNone(reply)
        self.assertEqual(status, STATUS_ACTIVE)

        # 3. Jogador 301 tenta enviar duas mensagens seguidas -> Bloqueado!
        reply, status = self.game_service.send_user_message(sess_id, "tester_human", "Mensagem dupla seguida")
        self.assertIsNone(reply)
        self.assertEqual(status, "Aguarde a resposta do outro jogador.")

        # 4. Jogador 302 responde -> Aceito!
        reply, status = self.game_service.send_user_message(sess_id, "pretend_bot", "Sim, sou um humano comum.")
        self.assertIsNone(reply)
        self.assertEqual(status, STATUS_ACTIVE)

        # 5. Ambos completam as 5 mensagens alternando (já enviaram 1 cada, faltam 4 cada)
        for i in range(2, 6):
            # Vez de 301
            _, s1 = self.game_service.send_user_message(sess_id, "tester_human", f"Pergunta {i}")
            self.assertEqual(s1, STATUS_ACTIVE)

            # Vez de 302
            _, s2 = self.game_service.send_user_message(sess_id, "pretend_bot", f"Resposta {i}")
            if i == 5:
                # Na 5ª resposta do segundo jogador, ambos completaram 5 turnos -> vai para VOTING!
                self.assertEqual(s2, STATUS_VOTING)
            else:
                self.assertEqual(s2, STATUS_ACTIVE)

        # 6. Verifica total de mensagens no banco
        messages = self.game_service.get_messages(sess_id)
        self.assertEqual(len(messages), 10)
        p1_msgs = [m for m in messages if m.sender_name == "tester_human"]
        p2_msgs = [m for m in messages if m.sender_name == "pretend_bot"]
        self.assertEqual(len(p1_msgs), 5)
        self.assertEqual(len(p2_msgs), 5)

if __name__ == "__main__":
    unittest.main()
