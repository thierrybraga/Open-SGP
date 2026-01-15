"""
Arquivo: app/modules/viability/models.py

Responsabilidade:
Modelos de Viabilidade Técnica para análise pré-venda.

Integrações:
- core.database
- shared.models
- modules.clients
- modules.plans
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ...core.database import Base
from ...shared.models import TimestampMixin


class ViabilityStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Viability(Base, TimestampMixin):
    __tablename__ = "viabilities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    address_id: Mapped[int | None] = mapped_column(ForeignKey("client_addresses.id", ondelete="SET NULL"), nullable=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), index=True)

    # Status e workflow
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)

    # Dados técnicos
    distance_to_pop: Mapped[float | None] = mapped_column(Float, nullable=True)  # em metros
    signal_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)  # excellent, good, fair, poor
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Equipamentos necessários
    equipment_needed: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    installation_complexity: Mapped[str | None] = mapped_column(String(20), nullable=True)  # low, medium, high

    # Observações
    technician_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auditoria
    analyzed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relacionamentos
    client = relationship("Client", back_populates="viabilities")
    plan = relationship("Plan")
    analyzer = relationship("User", foreign_keys=[analyzed_by])
