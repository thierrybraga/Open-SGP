"""
Arquivo: app/modules/discounts/models.py

Responsabilidade:
Modelos de Descontos por Plano e Forma de Pagamento.

Integrações:
- modules.plans.models
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class PlanDiscount(Base, TimestampMixin):
    """
    Desconto aplicável a um plano específico.
    """
    __tablename__ = "plan_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Tipo de desconto: percentage ou fixed
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Valor do desconto (percentual ou fixo)
    discount_value: Mapped[float] = mapped_column(Float, nullable=False)

    # Duração do desconto em meses (null = permanente)
    duration_months: Mapped[int | None] = mapped_column(nullable=True)

    # Ativo
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relação
    plan = relationship("Plan")

    __table_args__ = (
        Index("ix_plan_discounts_plan", "plan_id"),
        Index("ix_plan_discounts_active", "is_active"),
    )


class PaymentMethodDiscount(Base, TimestampMixin):
    """
    Desconto por forma de pagamento (portador bancário, débito automático, etc).
    """
    __tablename__ = "payment_method_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Método de pagamento: automatic_debit, credit_card, pix, etc
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Tipo de desconto: percentage ou fixed
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Valor do desconto (percentual ou fixo)
    discount_value: Mapped[float] = mapped_column(Float, nullable=False)

    # Aplicável a planos específicos (null = todos os planos)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), nullable=True)

    # Ativo
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relação
    plan = relationship("Plan")

    __table_args__ = (
        Index("ix_payment_method_discounts_method", "payment_method"),
        Index("ix_payment_method_discounts_active", "is_active"),
    )
