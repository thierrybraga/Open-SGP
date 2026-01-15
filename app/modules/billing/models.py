"""
Arquivo: app/modules/billing/models.py

Responsabilidade:
Modelos de Financeiro: Títulos, Remessas CNAB, Retornos CNAB, Pagamentos e Promessas.

Integrações:
- modules.contracts.models
- core.database
- shared.models
"""

from datetime import date, datetime
from sqlalchemy import String, Boolean, Float, ForeignKey, Index, Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class Title(Base, TimestampMixin):
    __tablename__ = "titles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), index=True)
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), index=True)  # open, paid, canceled, overdue

    fine_percent: Mapped[float] = mapped_column(Float, default=2.0)
    interest_percent: Mapped[float] = mapped_column(Float, default=1.0)

    bank_code: Mapped[str] = mapped_column(String(10), default="341")
    document_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    our_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    payment_slip_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bar_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    contract = relationship("Contract")

    __table_args__ = ()


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), index=True)
    payment_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(20))  # boleto, pix, cash

    title = relationship("Title")


class Remittance(Base, TimestampMixin):
    __tablename__ = "remittances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_titles: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="generated")


class RemittanceItem(Base, TimestampMixin):
    __tablename__ = "remittance_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    remittance_id: Mapped[int] = mapped_column(ForeignKey("remittances.id", ondelete="CASCADE"), index=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), index=True)
    value: Mapped[float] = mapped_column(Float)


class ReturnFile(Base, TimestampMixin):
    __tablename__ = "return_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(100))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0)


class ReturnItem(Base, TimestampMixin):
    __tablename__ = "return_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    return_file_id: Mapped[int] = mapped_column(ForeignKey("return_files.id", ondelete="CASCADE"), index=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # paid, canceled, other
    value: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[date] = mapped_column(Date)


class PaymentPromise(Base, TimestampMixin):
    __tablename__ = "payment_promises"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), index=True)
    title_id: Mapped[int | None] = mapped_column(ForeignKey("titles.id", ondelete="SET NULL"), nullable=True)
    promised_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, kept, broken
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)


class TitleAdjustment(Base, TimestampMixin):
    __tablename__ = "title_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(20))  # increase, discount
    amount: Mapped[float] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    title = relationship("Title")

    __table_args__ = (
        Index("ix_title_adjustments_type", "type"),
    )
