"""
Arquivo: app/modules/communication/models.py

Responsabilidade:
Modelos de comunicação: templates e fila de mensagens com status e controle
de reprocessamento.

Integrações:
- core.database
- shared.models
"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base
from ...shared.models import TimestampMixin


class Template(Base, TimestampMixin):
    __tablename__ = "comm_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    channel: Mapped[str] = mapped_column(String(20))  # sms, whatsapp, email
    content: Mapped[str] = mapped_column(String(2000))


class MessageQueue(Base, TimestampMixin):
    __tablename__ = "comm_message_queue"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(20))  # sms, whatsapp, email
    destination: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(2000))
    template_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # twilio, gatewaysms, whatsapp_api
    provider_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued, sent, failed
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
