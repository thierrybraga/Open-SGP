"""
Arquivo: app/modules/administration/employees/models.py

Responsabilidade:
Modelo de Funcionários/Colaboradores da empresa.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Date, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date

from ....core.database import Base
from ....shared.models import TimestampMixin


class Employee(Base, TimestampMixin):
    """
    Funcionário/Colaborador da empresa.
    """
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Dados Pessoais
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    document: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # CPF
    rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Contato
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Endereço
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Dados Profissionais
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Cargo
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Departamento
    admission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    termination_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Remuneração
    salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    payment_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # monthly, hourly, commission

    # Banco
    bank_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    bank_agency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)  # active, inactive, vacation, sick_leave
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Observações
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
