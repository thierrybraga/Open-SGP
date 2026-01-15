"""
Arquivo: app/modules/administration/finance/models.py

Responsabilidade:
Modelos de cadastros financeiros: Empresas, Portadores, Pontos de Recebimento,
Parâmetros Financeiros.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ....core.database import Base
from ....shared.models import TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150))
    legal_name: Mapped[str] = mapped_column(String(200))
    document: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # CNPJ
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Carrier(Base, TimestampMixin):
    __tablename__ = "carriers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    bank_code: Mapped[str] = mapped_column(String(10))
    agency: Mapped[str] = mapped_column(String(20))
    account: Mapped[str] = mapped_column(String(30))
    wallet: Mapped[str] = mapped_column(String(10))
    cnab_layout: Mapped[str] = mapped_column(String(3), default="400")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReceiptPoint(Base, TimestampMixin):
    __tablename__ = "receipt_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(255))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))

    company = relationship("Company")


class FinancialParameter(Base, TimestampMixin):
    __tablename__ = "financial_parameters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    default_carrier_id: Mapped[int | None] = mapped_column(ForeignKey("carriers.id", ondelete="SET NULL"), nullable=True)
    fine_percent: Mapped[float] = mapped_column(default=2.0)
    interest_percent: Mapped[float] = mapped_column(default=1.0)
    send_email_on_issue: Mapped[bool] = mapped_column(Boolean, default=False)

    company = relationship("Company")
    carrier = relationship("Carrier")
