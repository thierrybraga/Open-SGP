"""
Arquivo: app/modules/cashier/models.py

Responsabilidade:
Modelos de Caixa: Registros de caixa e movimentações.

Integrações:
- core.database
- shared.models
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class CashRegister(Base, TimestampMixin):
    __tablename__ = "cash_registers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)

    # Datas
    opened_at: Mapped[datetime] = mapped_column(index=True)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Valores
    opening_balance: Mapped[float] = mapped_column(Float, default=0.0)
    closing_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    difference: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)  # open, closed

    # Observações
    opening_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    closing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    operator = relationship("User", foreign_keys=[user_id])
    movements = relationship("CashMovement", back_populates="cash_register")


class CashMovement(Base, TimestampMixin):
    __tablename__ = "cash_movements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cash_register_id: Mapped[int] = mapped_column(ForeignKey("cash_registers.id", ondelete="CASCADE"), index=True)

    # Tipo de movimentação
    type: Mapped[str] = mapped_column(String(10), index=True)  # in (entrada), out (saída)
    category: Mapped[str] = mapped_column(String(50), index=True)  # payment, withdrawal, transfer, other

    # Valor
    amount: Mapped[float] = mapped_column(Float)

    # Referências
    title_id: Mapped[int | None] = mapped_column(ForeignKey("titles.id", ondelete="SET NULL"), nullable=True, index=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)

    # Forma de pagamento
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # cash, debit, credit, pix

    # Descrição
    description: Mapped[str] = mapped_column(Text)

    # Documento
    document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relacionamentos
    cash_register = relationship("CashRegister", back_populates="movements")
    title = relationship("Title")
    client = relationship("Client")
