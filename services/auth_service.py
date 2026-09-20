"""
services/auth_service.py
Serviço de Autenticação, Cadastro e Controle de Acesso Baseado em Perfis (RBAC).
"""

from typing import Optional, Tuple
from models.user import User, UserRepository
from core.security import (
    generate_salt,
    hash_password,
    verify_password,
    validate_username,
    validate_password_strength
)
from core.config import ROLE_USUARIO, ROLE_OPERADOR, ROLE_ADMIN
from core.database import log_audit_event

class AuthService:
    @staticmethod
    def authenticate(username: str, password: str) -> Tuple[Optional[User], str]:
        """
        Autentica o usuário com proteção contra senhas inválidas e checagem de status ativo.
        Retorna (User, "") em caso de sucesso, ou (None, mensagem_de_erro).
        """
        username = username.strip()
        user = UserRepository.get_by_username(username)
        if not user:
            return None, "Usuário ou senha incorretos."

        if not user.is_active:
            return None, "Esta conta está inativa ou bloqueada pelo administrador."

        if not verify_password(password, user.salt, user.password_hash):
            log_audit_event(user.id, "LOGIN_FAILED", f"Tentativa de login com senha incorreta para {username}")
            return None, "Usuário ou senha incorretos."

        log_audit_event(user.id, "LOGIN_SUCCESS", f"Usuário {username} realizou login com sucesso")
        return user, ""

    @staticmethod
    def register(username: str, full_name: str, password: str, confirm_password: str) -> Tuple[Optional[User], str]:
        """
        Registra um novo usuário no sistema com perfil inicial 'usuario'.
        """
        valid_user, err_user = validate_username(username)
        if not valid_user:
            return None, err_user

        if not full_name or len(full_name.strip()) < 2:
            return None, "Informe um nome completo válido."

        if password != confirm_password:
            return None, "As senhas não coincidem."

        valid_pwd, err_pwd = validate_password_strength(password)
        if not valid_pwd:
            return None, err_pwd

        # Verifica duplicidade de usuário
        existing = UserRepository.get_by_username(username)
        if existing:
            return None, "Este nome de usuário já está em uso."

        salt = generate_salt()
        pwd_hash = hash_password(password, salt)
        new_user = UserRepository.create(
            username=username,
            full_name=full_name,
            password_hash=pwd_hash,
            salt=salt,
            role=ROLE_USUARIO
        )

        log_audit_event(new_user.id, "USER_REGISTERED", f"Novo usuário {username} cadastrado com sucesso")
        return new_user, ""

    @staticmethod
    def has_role(user: Optional[User], allowed_roles: list[str]) -> bool:
        """Verifica se o usuário possui um dos papéis permitidos para a ação."""
        if not user or not user.is_active:
            return False
        return user.role in allowed_roles
