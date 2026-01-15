"""
Arquivo: app/modules/contracts/models.py

Responsabilidade:
Modelo de Contrato relacionando Cliente e Plano, com status, datas e parâmetros
comerciais e operacionais básicos.

Integrações:
- modules.clients.models
- modules.plans.models
- core.database
- shared.models
"""

from datetime import date
from sqlalchemy import String, Boolean, Float, ForeignKey, Index, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), index=True)

    status: Mapped[str] = mapped_column(String(20), index=True)  # pending, active, suspended, canceled
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    installation_address: Mapped[str] = mapped_column(String(500))
    billing_day: Mapped[int] = mapped_column(default=10)
    suspend_on_arrears: Mapped[bool] = mapped_column(Boolean, default=True)

    loyalty_months: Mapped[int] = mapped_column(default=0)
    price_override: Mapped[float | None] = mapped_column(Float, nullable=True)

    client = relationship("Client")
    plan = relationship("Plan")
    addendums = relationship("ContractAddendum", back_populates="contract")

    __table_args__ = ()
