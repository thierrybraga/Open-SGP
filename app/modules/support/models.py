"""
Arquivo: app/modules/support/models.py

Responsabilidade:
Modelos de dados para tickets de suporte, categorias e mensagens.

Integrações:
- modules.clients.models
- modules.contracts.models
- modules.auth.models (Users)
- core.database
"""

from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin

class TicketCategory(Base, TimestampMixin):
    __tablename__ = "support_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Ticket(Base, TimestampMixin):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    protocol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id"), nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("support_categories.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="normal") # low, normal, high, critical
    status: Mapped[str] = mapped_column(String(20), default="open") # open, in_progress, pending, closed, canceled
    origin: Mapped[str] = mapped_column(String(20), default="manual") # manual, email, whatsapp, customer_app
    
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    client = relationship("Client")
    contract = relationship("Contract")
    category = relationship("TicketCategory")
    assignee = relationship("User", foreign_keys=[assignee_id])
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class TicketMessage(Base, TimestampMixin):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True) # Null if system or client (via app)
    
    content: Mapped[str] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    attachment_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    ticket = relationship("Ticket", back_populates="messages")
    user = relationship("User")


class Occurrence(Base, TimestampMixin):
    __tablename__ = "occurrences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id"), nullable=True, index=True)
    
    category: Mapped[str] = mapped_column(String(50), default="general")
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, critical
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, closed
    
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("support_tickets.id"), nullable=True)
    service_order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Placeholder until SO module exists
    
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    client = relationship("Client")
    contract = relationship("Contract")
    ticket = relationship("Ticket")
