"""
Arquivo: app/modules/service_orders/models.py

Responsabilidade:
Modelos de Ordem de Serviço e itens, com agendamento, técnico, status e
relacionamentos com Cliente/Contrato/Ticket.

Integrações:
- modules.clients.models
- modules.contracts.models
- modules.support.models
- core.database
- shared.models
"""

from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class ServiceOrder(Base, TimestampMixin):
    __tablename__ = "service_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("support_tickets.id", ondelete="SET NULL"), nullable=True)

    type: Mapped[str] = mapped_column(String(30))  # install, repair, relocation, cancel
    priority: Mapped[str] = mapped_column(String(20))  # low, medium, high, urgent
    status: Mapped[str] = mapped_column(String(20), index=True)  # open, scheduled, in_progress, completed, canceled
    technician_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    items = relationship("ServiceOrderItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_service_orders_type", "type"),
    )


class ServiceOrderItem(Base, TimestampMixin):
    __tablename__ = "service_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("service_orders.id", ondelete="CASCADE"), index=True)
    description: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    done: Mapped[bool] = mapped_column(Boolean, default=False)

    order = relationship("ServiceOrder", back_populates="items")
