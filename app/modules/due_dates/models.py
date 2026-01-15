"""
Arquivo: app/modules/due_dates/models.py

Responsabilidade:
Modelo de Configuração de Vencimentos.
"""

from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class DueDateConfig(Base, TimestampMixin):
    __tablename__ = "due_date_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Configuração específica
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), nullable=True, index=True)

    # Dia do vencimento (1-31)
    due_day: Mapped[int] = mapped_column(Integer)

    # Observações
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Prioridade: client > plan > global
    priority: Mapped[str] = mapped_column(String(20), default="global")  # client, plan, global

    # Relacionamentos
    client = relationship("Client", foreign_keys=[client_id])
    plan = relationship("Plan", foreign_keys=[plan_id])
