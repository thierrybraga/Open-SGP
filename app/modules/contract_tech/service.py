"""
Arquivo: app/modules/contract_tech/service.py

Responsabilidade:
Regras de negócio para informações técnicas: registrar equipamentos, medições de
sinal, speedtests e logs técnicos.

Integrações:
- modules.contract_tech.models
"""

from sqlalchemy.orm import Session
from .models import ContractEquipment, SignalMeasurement, SpeedTest, TechLog
from .schemas import EquipmentCreate, SignalCreate, SpeedTestCreate, TechLogCreate


def register_equipment(db: Session, data: EquipmentCreate) -> ContractEquipment:
    eq = ContractEquipment(**data.dict())
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


def register_signal(db: Session, data: SignalCreate) -> SignalMeasurement:
    sm = SignalMeasurement(**data.dict())
    db.add(sm)
    db.commit()
    db.refresh(sm)
    return sm


def register_speedtest(db: Session, data: SpeedTestCreate) -> SpeedTest:
    st = SpeedTest(**data.dict())
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


def register_techlog(db: Session, data: TechLogCreate) -> TechLog:
    tl = TechLog(**data.dict())
    db.add(tl)
    db.commit()
    db.refresh(tl)
    return tl

