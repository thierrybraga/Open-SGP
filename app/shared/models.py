"""
Arquivo: app/shared/models.py

Responsabilidade:
Define mixins e utilitários comuns de modelos, como timestamps e campos padrão.

Integrações:
- core.database
- modules.* modelos
"""

from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

