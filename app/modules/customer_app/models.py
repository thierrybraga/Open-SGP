"""
Arquivo: app/modules/customer_app/models.py

Responsabilidade:
Modelos do App do Cliente: preferências e tokens de notificação.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base
from ...shared.models import TimestampMixin


class CustomerPreference(Base, TimestampMixin):
    __tablename__ = "customer_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)


class DeviceToken(Base, TimestampMixin):
    __tablename__ = "customer_device_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(20))
    token: Mapped[str] = mapped_column(String(200))

