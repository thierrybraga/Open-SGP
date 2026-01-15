"""
Arquivo: app/modules/referrals/models.py

Responsabilidade:
Modelos de Indicações e Recompensas.

Integrações:
- modules.clients.models
- modules.contracts.models
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class Referral(Base, TimestampMixin):
    """
    Indicação de um cliente por outro.
    """
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Cliente que indicou (referrer)
    referrer_client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)

    # Cliente indicado (referred)
    referred_client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)

    # Contrato do cliente indicado (quando convertido)
    referred_contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)

    # Status da indicação
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # pending, converted, rewarded, cancelled

    # Data de conversão (quando virou cliente ativo)
    converted_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Código de indicação (opcional, para rastreamento)
    referral_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Observações
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relações
    referrer = relationship("Client", foreign_keys=[referrer_client_id])
    referred = relationship("Client", foreign_keys=[referred_client_id])
    contract = relationship("Contract")


class ReferralReward(Base, TimestampMixin):
    """
    Recompensa por indicação.
    """
    __tablename__ = "referral_rewards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Indicação relacionada
    referral_id: Mapped[int] = mapped_column(ForeignKey("referrals.id", ondelete="CASCADE"), index=True)

    # Tipo de recompensa
    reward_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # discount, cash, credit, bonus

    # Valor da recompensa
    reward_value: Mapped[float] = mapped_column(Float, nullable=False)

    # Moeda/unidade (BRL, USD, meses, etc)
    currency: Mapped[str] = mapped_column(String(10), default="BRL")

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # pending, approved, paid, cancelled

    # Data de pagamento/aplicação
    paid_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Referência de pagamento
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Descrição
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relação
    referral = relationship("Referral")


class ReferralProgram(Base, TimestampMixin):
    """
    Configuração do programa de indicações.
    """
    __tablename__ = "referral_programs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Nome do programa
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Tipo de recompensa padrão
    default_reward_type: Mapped[str] = mapped_column(String(20), default="discount")

    # Valor padrão da recompensa
    default_reward_value: Mapped[float] = mapped_column(Float, default=0.0)

    # Recompensa para o indicado também?
    reward_referred_client: Mapped[bool] = mapped_column(Boolean, default=False)

    # Valor da recompensa para o indicado
    referred_reward_value: Mapped[float] = mapped_column(Float, default=0.0)

    # Número mínimo de meses que o indicado deve ficar ativo
    min_active_months: Mapped[int] = mapped_column(Integer, default=1)

    # Limite de indicações por cliente (0 = ilimitado)
    max_referrals_per_client: Mapped[int] = mapped_column(Integer, default=0)

    # Ativo
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Validade
    valid_from: Mapped[str | None] = mapped_column(String(30), nullable=True)
    valid_until: Mapped[str | None] = mapped_column(String(30), nullable=True)
