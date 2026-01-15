"""
Arquivo: app/modules/audit/models.py

Responsabilidade:
Model para registro de auditoria.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """
    Registra todas as mudanças importantes no sistema.

    Campos:
    - user_id: ID do usuário que fez a ação
    - action: tipo de ação (CREATE, UPDATE, DELETE, LOGIN, etc.)
    - entity_type: tipo de entidade (Contract, Client, etc.)
    - entity_id: ID da entidade afetada
    - old_values: valores antigos (JSON)
    - new_values: valores novos (JSON)
    - ip_address: IP do usuário
    - user_agent: User agent do navegador
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    username = Column(String(100), index=True)
    action = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    entity_type = Column(String(100), nullable=False, index=True)  # Contract, Client, User, etc.
    entity_id = Column(Integer, nullable=True, index=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 pode ter até 45 chars
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
