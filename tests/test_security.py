"""
tests/test_security.py
Testes unitários para o módulo de segurança e hashing criptográfico.
"""

import unittest
from core.security import (
    generate_salt,
    hash_password,
    verify_password,
    validate_username,
    validate_password_strength
)

class TestSecurity(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        password = "MinhaSenhaSegura123!"
        salt = generate_salt()
        pwd_hash = hash_password(password, salt)
        
        # Deve verificar com sucesso a senha correta
        self.assertTrue(verify_password(password, salt, pwd_hash))
        
        # Deve rejeitar senha errada
        self.assertFalse(verify_password("SenhaErrada", salt, pwd_hash))

    def test_unique_salts_produce_different_hashes(self):
        password = "mesmasenha"
        salt1 = generate_salt()
        salt2 = generate_salt()
        
        hash1 = hash_password(password, salt1)
        hash2 = hash_password(password, salt2)
        
        self.assertNotEqual(hash1, hash2)

    def test_validate_username(self):
        valid, _ = validate_username("jogador_01")
        self.assertTrue(valid)

        invalid_len, _ = validate_username("ab")
        self.assertFalse(invalid_len)

        invalid_chars, _ = validate_username("user!@#$")
        self.assertFalse(invalid_chars)

    def test_validate_password_strength(self):
        valid, _ = validate_password_strength("123456")
        self.assertTrue(valid)

        invalid, _ = validate_password_strength("12345")
        self.assertFalse(invalid)

if __name__ == "__main__":
    unittest.main()
