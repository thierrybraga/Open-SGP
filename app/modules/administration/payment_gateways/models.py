"""
Arquivo: app/modules/administration/payment_gateways/models.py

Responsabilidade:
Modelos de Gateways de Pagamento para integração com provedores externos.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ....core.database import Base
from ....shared.models import TimestampMixin


class PaymentGateway(Base, TimestampMixin):
    """
    Gateway de pagamento (PIX, cartão de crédito, boleto, etc).
    """
    __tablename__ = "payment_gateways"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Identificação
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # pagarme, mercadopago, asaas, etc

    # Tipo de pagamento suportado
    payment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pix, credit_card, boleto, debit_card

    # Credenciais (JSON para flexibilidade)
    credentials: Mapped[dict] = mapped_column(JSON, nullable=False)  # api_key, secret_key, etc

    # Configurações (JSON)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # taxas, prazos, etc

    # Ambiente
    environment: Mapped[str] = mapped_column(String(20), default="sandbox")  # sandbox, production

    # Webhook
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Observações
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
