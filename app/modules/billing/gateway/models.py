"""
Arquivo: app/modules/billing/gateway/models.py

Responsabilidade:
Modelos de Gateway de Pagamento: configuração e registros de cobrança.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, ForeignKey, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ....core.database import Base
from ....shared.models import TimestampMixin


class PaymentGatewayConfig(Base, TimestampMixin):
    __tablename__ = "payment_gateway_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50))  # asaas, gerencianet, stripe
    api_key: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hmac_algorithm: Mapped[str] = mapped_column(String(10), default="sha256")


class PaymentCharge(Base, TimestampMixin):
    __tablename__ = "payment_charges"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"))
    gateway_id: Mapped[int] = mapped_column(ForeignKey("payment_gateway_configs.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="created")  # created, paid, canceled
    reference: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    payment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    gateway = relationship("PaymentGatewayConfig")

    __table_args__ = (
        Index("ix_payment_charges_reference", "reference"),
    )
