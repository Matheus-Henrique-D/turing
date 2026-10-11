"""
tests/test_matchmaking.py
Testes unitários para o sistema de matchmaking multijogador em tempo real.
"""

import unittest
from core.database import init_db, get_db_connection
from core.security import generate_salt, hash_password
from models.session import SessionRepository
from services.matchmaking_service import MatchmakingService

class TestMatchmaking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        # Garante que os usuários de teste existam para respeitar as Foreign Keys
        with get_db_connection() as conn:
            salt = generate_salt()
            pwd = hash_password("senha123", salt)
            for uid, uname in [(201, "player_alpha"), (202, "player_beta"), (203, "player_gamma")]:
                conn.execute("""
                INSERT OR IGNORE INTO users (id, username, full_name, password_hash, salt, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 'usuario', 1, '2026-01-01T00:00:00')
                """, (uid, uname, f"Nome {uname}", pwd, salt))

    def tearDown(self):
        MatchmakingService.leave_queue(201)
        MatchmakingService.leave_queue(202)
        MatchmakingService.leave_queue(203)

    def test_queue_and_peer_matching(self):
        # 1. Jogador 1 entra na fila
        res1 = MatchmakingService.join_queue(user_id=201, username="player_alpha")
        self.assertEqual(res1["status"], "waiting")

        # 2. Jogador 2 entra na fila -> Deve ocorrer MATCH imediato!
        res2 = MatchmakingService.join_queue(user_id=202, username="player_beta")
        self.assertEqual(res2["status"], "matched")
        self.assertIsNotNone(res2["session_id"])

        # 3. Jogador 1 consulta a fila -> Deve detectar que foi pareado na mesma sessão!
        res1_poll = MatchmakingService.poll_queue_status(user_id=201, username="player_alpha")
        self.assertEqual(res1_poll["status"], "matched")
        self.assertEqual(res1_poll["session_id"], res2["session_id"])

        # 4. Verifica a sessão criada
        session = SessionRepository.get_by_id(res2["session_id"])
        self.assertIsNotNone(session)
        self.assertTrue(session.is_multiplayer)
        self.assertEqual(session.opponent_type, "HUMAN")
        self.assertEqual(session.user_id, 202)
        self.assertEqual(session.player2_id, 201)

    def test_leave_queue(self):
        MatchmakingService.join_queue(user_id=203, username="player_gamma")
        self.assertGreaterEqual(MatchmakingService.get_waiting_count(), 1)

        MatchmakingService.leave_queue(user_id=203)
        # Ao sair, não deve mais estar na fila
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM matchmaking_queue WHERE user_id = ?", (203,))
            row = cursor.fetchone()
            self.assertIsNone(row)

if __name__ == "__main__":
    unittest.main()
