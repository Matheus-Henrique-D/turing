"""
services/admin_service.py
Serviço do Painel de Administração: Gestão de Usuários (RBAC), Métricas Globais e Logs de Auditoria.
"""

from typing import Tuple
from models.user import User, UserRepository
from models.session import SessionRepository
from core.config import ALL_ROLES
from core.database import get_db_connection, log_audit_event

class AdminService:
    @staticmethod
    def list_all_users() -> list[User]:
        return UserRepository.list_all()

    @staticmethod
    def change_user_role(admin_user: User, target_user_id: int, new_role: str) -> Tuple[bool, str]:
        """Altera o papel RBAC de um usuário ('usuario', 'operador', 'admin')."""
        if new_role not in ALL_ROLES:
            return False, f"Papel inválido. Escolha entre: {', '.join(ALL_ROLES)}"

        target = UserRepository.get_by_id(target_user_id)
        if not target:
            return False, "Usuário não encontrado."

        if target.id == admin_user.id and new_role != "admin":
            return False, "O administrador não pode remover seu próprio perfil de admin."

        success = UserRepository.update_role(target_user_id, new_role)
        if success:
            log_audit_event(
                admin_user.id,
                "ADMIN_ROLE_CHANGE",
                f"Admin {admin_user.username} alterou perfil do usuário {target.username} para '{new_role}'"
            )
            return True, f"Perfil de {target.username} atualizado para '{new_role}' com sucesso."
        return False, "Erro ao atualizar perfil no banco de dados."

    @staticmethod
    def toggle_user_active(admin_user: User, target_user_id: int, is_active: bool) -> Tuple[bool, str]:
        """Ativa ou bloqueia o acesso de um usuário ao sistema."""
        target = UserRepository.get_by_id(target_user_id)
        if not target:
            return False, "Usuário não encontrado."

        if target.id == admin_user.id:
            return False, "O administrador não pode desativar a si próprio."

        success = UserRepository.toggle_active(target_user_id, is_active)
        if success:
            status_str = "ativado" if is_active else "bloqueado"
            log_audit_event(
                admin_user.id,
                "ADMIN_STATUS_CHANGE",
                f"Admin {admin_user.username} alterou status de {target.username} para '{status_str}'"
            )
            return True, f"Usuário {target.username} {status_str} com sucesso."
        return False, "Erro ao atualizar status."

    @staticmethod
    def get_dashboard_metrics() -> dict:
        """Calcula métricas consolidadas de desempenho e uso do sistema."""
        global_stats = SessionRepository.get_global_stats()
        
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN role = 'usuario' THEN 1 ELSE 0 END) as total_players,
                SUM(CASE WHEN role = 'operador' THEN 1 ELSE 0 END) as total_operators,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as total_admins
            FROM users
            """)
            u_row = cursor.fetchone()

        return {
            "total_users": u_row["total_users"] or 0,
            "total_players": u_row["total_players"] or 0,
            "total_operators": u_row["total_operators"] or 0,
            "total_admins": u_row["total_admins"] or 0,
            **global_stats
        }

    @staticmethod
    def get_audit_logs(limit: int = 50) -> list[dict]:
        """Recupera os registros mais recentes da trilha de auditoria."""
        with get_db_connection() as conn:
            cursor = conn.execute("""
            SELECT al.*, u.username
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.id DESC
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
