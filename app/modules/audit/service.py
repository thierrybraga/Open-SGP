"""
Arquivo: app/modules/audit/service.py

Responsabilidade:
Serviço para criar registros de auditoria.
"""

from sqlalchemy.orm import Session
from app.modules.audit.models import AuditLog
from typing import Optional, Dict, Any
from datetime import datetime


class AuditService:
    """Serviço de auditoria"""

    @staticmethod
    def log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Cria um registro de auditoria.

        Args:
            action: Tipo de ação (CREATE, UPDATE, DELETE, LOGIN, etc.)
            entity_type: Tipo de entidade (Contract, Client, User, etc.)
            entity_id: ID da entidade
            user_id: ID do usuário
            username: Nome do usuário
            old_values: Valores antigos (dict)
            new_values: Valores novos (dict)
            description: Descrição adicional
            ip_address: IP do cliente
            user_agent: User agent
        """
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def get_entity_history(
        db: Session,
        entity_type: str,
        entity_id: int,
        limit: int = 50
    ) -> list[AuditLog]:
        """Retorna histórico de mudanças de uma entidade"""
        return (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_user_actions(
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> list[AuditLog]:
        """Retorna ações de um usuário"""
        return (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
