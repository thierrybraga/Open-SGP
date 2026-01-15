"""
Arquivo: app/modules/contract_tech/models.py

Responsabilidade:
Modelos de informações técnicas por contrato: equipamentos, medições de sinal,
testes de velocidade e logs técnicos.

Integrações:
- modules.contracts.models
- core.database
- shared.models
"""

from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class ContractEquipment(Base, TimestampMixin):
    __tablename__ = "contract_equipments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"))
    device_type: Mapped[str] = mapped_column(String(30))  # onu, router, radio
    vendor: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(60))
    serial_number: Mapped[str] = mapped_column(String(60))
    installed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class SignalMeasurement(Base, TimestampMixin):
    __tablename__ = "signal_measurements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"))
    rx_level_dbm: Mapped[float] = mapped_column(Float)
    tx_level_dbm: Mapped[float] = mapped_column(Float)
    snr_db: Mapped[float] = mapped_column(Float)
    measured_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class SpeedTest(Base, TimestampMixin):
    __tablename__ = "speed_tests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"))
    download_mbps: Mapped[float] = mapped_column(Float)
    upload_mbps: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[int] = mapped_column(Integer)
    jitter_ms: Mapped[int] = mapped_column(Integer)
    tested_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class TechLog(Base, TimestampMixin):
    __tablename__ = "tech_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"))
    event: Mapped[str] = mapped_column(String(60))
    details: Mapped[str] = mapped_column(String(500))
    occurred_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

