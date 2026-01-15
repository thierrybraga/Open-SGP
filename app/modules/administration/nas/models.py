"""
Arquivo: app/modules/administration/nas/models.py

Responsabilidade:
Modelo de NAS com vínculo ao POP e credenciais de acesso.

Integrações:
- core.database
- shared.models
- modules.administration.pops.models
"""

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ....core.database import Base
from ....shared.models import TimestampMixin


class NAS(Base, TimestampMixin):
    __tablename__ = "nas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(50), index=True)
    secret: Mapped[str] = mapped_column(String(255))
    vendor: Mapped[str] = mapped_column(String(50))

    pop_id: Mapped[int | None] = mapped_column(ForeignKey("pops.id", ondelete="SET NULL"), nullable=True)
    pop = relationship("POP", back_populates="nas_devices")

