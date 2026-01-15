"""
Arquivo: app/modules/technician_app/models.py

Responsabilidade:
Modelos do App do Técnico: perfil do técnico, logs de trabalho e materiais
utilizados por ordem de serviço.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base
from ...shared.models import TimestampMixin


class TechnicianProfile(Base, TimestampMixin):
    __tablename__ = "technician_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30))
    skills: Mapped[str] = mapped_column(String(200))


class TechnicianWorkLog(Base, TimestampMixin):
    __tablename__ = "technician_work_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("service_orders.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(String(1000))


class TechnicianMaterialUsage(Base, TimestampMixin):
    __tablename__ = "technician_material_usages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("service_orders.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id", ondelete="RESTRICT"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

