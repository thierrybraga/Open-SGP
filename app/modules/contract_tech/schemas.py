"""
Arquivo: app/modules/contract_tech/schemas.py

Responsabilidade:
Esquemas Pydantic para equipamentos, medições de sinal, speedtest e logs.

Integrações:
- modules.contract_tech.models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EquipmentCreate(BaseModel):
    contract_id: int
    device_type: str
    vendor: str
    model: str
    serial_number: str


class EquipmentOut(EquipmentCreate):
    id: int
    installed_at: datetime

    class Config:
        from_attributes = True


class SignalCreate(BaseModel):
    contract_id: int
    rx_level_dbm: float
    tx_level_dbm: float
    snr_db: float


class SignalOut(SignalCreate):
    id: int
    measured_at: datetime

    class Config:
        from_attributes = True


class SpeedTestCreate(BaseModel):
    contract_id: int
    download_mbps: float
    upload_mbps: float
    latency_ms: int
    jitter_ms: int


class SpeedTestOut(SpeedTestCreate):
    id: int
    tested_at: datetime

    class Config:
        from_attributes = True


class TechLogCreate(BaseModel):
    contract_id: int
    event: str
    details: str


class TechLogOut(TechLogCreate):
    id: int
    occurred_at: datetime

    class Config:
        from_attributes = True

