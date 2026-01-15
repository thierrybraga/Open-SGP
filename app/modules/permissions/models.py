"""
Arquivo: app/modules/permissions/models.py

Responsabilidade:
Modelo de Permission e associação com Role.

Integrações:
- core.database
- modules.roles.models
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255))

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")

