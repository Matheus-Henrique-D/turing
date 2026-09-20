"""
tests/test_auth.py
Testes unitários para autenticação, cadastro e controle de perfis RBAC.
"""

import unittest
from core.database import init_db
from services.auth_service import AuthService
from core.config import ROLE_USUARIO, ROLE_OPERADOR, ROLE_ADMIN

class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_default_admin_login(self):
        user, err = AuthService.authenticate("admin", "admin123")
        self.assertIsNotNone(user)
        self.assertEqual(user.role, ROLE_ADMIN)
        self.assertEqual(err, "")

    def test_invalid_login(self):
        user, err = AuthService.authenticate("admin", "senha_incorreta")
        self.assertIsNone(user)
        self.assertIn("incorretos", err)

    def test_register_and_login_new_user(self):
        import uuid
        uname = f"user_{uuid.uuid4().hex[:6]}"
        user, err = AuthService.register(uname, "Usuario Teste", "senha123", "senha123")
        self.assertIsNotNone(user)
        self.assertEqual(user.role, ROLE_USUARIO)

        # Login com novo usuário
        logged, l_err = AuthService.authenticate(uname, "senha123")
        self.assertIsNotNone(logged)
        self.assertEqual(logged.username, uname)

    def test_rbac_permissions(self):
        admin_user, _ = AuthService.authenticate("admin", "admin123")
        self.assertTrue(AuthService.has_role(admin_user, [ROLE_ADMIN]))
        self.assertFalse(AuthService.has_role(admin_user, [ROLE_USUARIO]))

if __name__ == "__main__":
    unittest.main()
