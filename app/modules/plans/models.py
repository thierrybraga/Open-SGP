"""
Arquivo: app/modules/plans/models.py

Responsabilidade:
Modelo de Plano com categorias (internet, tv), atributos técnicos e comerciais.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base
from ...shared.models import TimestampMixin


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(20))  # internet, tv
    description: Mapped[str] = mapped_column(String(500))

    download_speed_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    upload_speed_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    burst_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    burst_rate_percent: Mapped[float] = mapped_column(Float, default=0.0)
    burst_threshold_seconds: Mapped[int] = mapped_column(default=0)

    price: Mapped[float] = mapped_column(Float, default=0.0)
    loyalty_months: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_plans_category", "category"),
        Index("ix_plans_active", "is_active"),
    )

