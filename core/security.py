"""
core/security.py
Módulo de segurança, criptografia de senhas e sanitização de dados.
Implementa PBKDF2-HMAC-SHA256 com salt único por usuário e comparação em tempo constante.
"""

import hashlib
import os
import re
import hmac
from core.config import PASSWORD_SALT_BYTES, PASSWORD_HASH_ITERATIONS, MIN_PASSWORD_LENGTH

def generate_salt() -> str:
    """Gera um salt criptograficamente seguro em hexadecimal."""
    return os.urandom(PASSWORD_SALT_BYTES).hex()

def hash_password(password: str, salt: str) -> str:
    """
    Gera o hash PBKDF2-HMAC-SHA256 para a senha combinada com o salt.
    """
    pwd_bytes = password.encode("utf-8")
    salt_bytes = bytes.fromhex(salt)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        pwd_bytes,
        salt_bytes,
        PASSWORD_HASH_ITERATIONS
    )
    return key.hex()

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """
    Verifica se a senha informada corresponde ao hash esperado utilizando
    comparação em tempo constante (mitigando ataques de temporização).
    """
    computed = hash_password(password, salt)
    return hmac.compare_digest(computed, expected_hash)

def validate_username(username: str) -> tuple[bool, str]:
    """
    Valida o nome de usuário (regras de formato e caracteres permitidos).
    """
    if not username:
        return False, "O nome de usuário não pode estar vazio."
    
    username = username.strip()
    if len(username) < 3 or len(username) > 30:
        return False, "O nome de usuário deve ter entre 3 e 30 caracteres."
        
    if not re.match(r"^[a-zA-Z0-9_\.]+$", username):
        return False, "O nome de usuário pode conter apenas letras, números, '_' e '.'."
        
    return True, ""

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida os critérios mínimos de segurança para a senha.
    """
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"A senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres."
        
    return True, ""
