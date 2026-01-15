"""
Arquivo: app/modules/administration/operation_points/models.py

Responsabilidade:
Modelo de Pontos de Operação (locais de atendimento, escritórios, lojas).

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Float, Time
from sqlalchemy.orm import Mapped, mapped_column

from ....core.database import Base
from ....shared.models import TimestampMixin


class OperationPoint(Base, TimestampMixin):
    """
    Ponto de Operação: escritório, loja, ponto de atendimento.
    """
    __tablename__ = "operation_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Informações básicas
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Tipo de ponto
    point_type: Mapped[str] = mapped_column(String(50), nullable=False)  # office, store, service_center, warehouse

    # Endereço
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Coordenadas geográficas
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Contato
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Horário de funcionamento
    opening_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM
    closing_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM
    working_days: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "mon,tue,wed,thu,fri"

    # Responsável
    manager_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    manager_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Observações
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
