"""
Arquivo: app/modules/administration/pops/models.py

Responsabilidade:
Modelo de POP (Point of Presence) com informações geográficas e relacionamento
com dispositivos NAS.

Integrações:
- core.database
- shared.models
- modules.administration.nas.models
"""

from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ....core.database import Base
from ....shared.models import TimestampMixin


class POP(Base, TimestampMixin):
    __tablename__ = "pops"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    city: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    nas_devices = relationship("NAS", back_populates="pop")

