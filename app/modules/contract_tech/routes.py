"""
Arquivo: app/modules/contract_tech/routes.py

Responsabilidade:
Rotas REST para informações técnicas do contrato: equipamentos, sinal, speedtest
e logs técnicos.

Integrações:
- core.dependencies
- modules.contract_tech.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import ContractEquipment, SignalMeasurement, SpeedTest, TechLog
from .schemas import (
    EquipmentCreate,
    EquipmentOut,
    SignalCreate,
    SignalOut,
    SpeedTestCreate,
    SpeedTestOut,
    TechLogCreate,
    TechLogOut,
)
from .service import (
    register_equipment,
    register_signal,
    register_speedtest,
    register_techlog,
)


router = APIRouter()


@router.get("/equipment/{contract_id}", response_model=List[EquipmentOut])
def list_equipment(contract_id: int, db: Session = Depends(get_db)):
    items = db.query(ContractEquipment).filter(ContractEquipment.contract_id == contract_id).all()
    return [EquipmentOut(**e.__dict__) for e in items]


@router.post("/equipment", response_model=EquipmentOut, dependencies=[Depends(require_permissions("contract_tech.equipment.create"))])
def register_equipment_endpoint(data: EquipmentCreate, db: Session = Depends(get_db)):
    e = register_equipment(db, data)
    return EquipmentOut(**e.__dict__)


@router.get("/signal/{contract_id}", response_model=List[SignalOut])
def list_signal(contract_id: int, db: Session = Depends(get_db)):
    items = db.query(SignalMeasurement).filter(SignalMeasurement.contract_id == contract_id).all()
    return [SignalOut(**s.__dict__) for s in items]


@router.post("/signal", response_model=SignalOut, dependencies=[Depends(require_permissions("contract_tech.signal.create"))])
def register_signal_endpoint(data: SignalCreate, db: Session = Depends(get_db)):
    s = register_signal(db, data)
    return SignalOut(**s.__dict__)


@router.get("/speedtest/{contract_id}", response_model=List[SpeedTestOut])
def list_speedtests(contract_id: int, db: Session = Depends(get_db)):
    items = db.query(SpeedTest).filter(SpeedTest.contract_id == contract_id).all()
    return [SpeedTestOut(**st.__dict__) for st in items]


@router.post("/speedtest", response_model=SpeedTestOut, dependencies=[Depends(require_permissions("contract_tech.speedtest.create"))])
def register_speedtest_endpoint(data: SpeedTestCreate, db: Session = Depends(get_db)):
    st = register_speedtest(db, data)
    return SpeedTestOut(**st.__dict__)


@router.get("/logs/{contract_id}", response_model=List[TechLogOut])
def list_logs(contract_id: int, db: Session = Depends(get_db)):
    items = db.query(TechLog).filter(TechLog.contract_id == contract_id).all()
    return [TechLogOut(**l.__dict__) for l in items]


@router.post("/logs", response_model=TechLogOut, dependencies=[Depends(require_permissions("contract_tech.logs.create"))])
def register_log_endpoint(data: TechLogCreate, db: Session = Depends(get_db)):
    l = register_techlog(db, data)
    return TechLogOut(**l.__dict__)

