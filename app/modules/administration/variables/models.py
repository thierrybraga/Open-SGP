"""
Arquivo: app/modules/administration/variables/models.py

Responsabilidade:
Modelo de variáveis de sistema para configurações globais.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ....core.database import Base
from ....shared.models import TimestampMixin


class SystemVariable(Base, TimestampMixin):
    __tablename__ = "system_variables"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(String(255))

