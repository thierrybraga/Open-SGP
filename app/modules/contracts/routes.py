"""
Arquivo: app/modules/contracts/routes.py

Responsabilidade:
Rotas REST para contratos, com filtros por cliente, plano, status e datas.

Integrações:
- core.dependencies
- modules.contracts.service
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Contract
from .schemas import ContractCreate, ContractUpdate, ContractOut
from .service import create_contract, update_contract


router = APIRouter()


@router.get("/", response_model=List[ContractOut])
def list_contracts(
    client_id: Optional[int] = Query(default=None),
    plan_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    start_from: Optional[date] = Query(default=None),
    start_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Contract)
    if client_id:
        q = q.filter(Contract.client_id == client_id)
    if plan_id:
        q = q.filter(Contract.plan_id == plan_id)
    if status:
        q = q.filter(Contract.status == status)
    if start_from:
        q = q.filter(Contract.start_date >= start_from)
    if start_to:
        q = q.filter(Contract.start_date <= start_to)
    items = q.all()
    return [ContractOut(**c.__dict__) for c in items]


@router.post("/", response_model=ContractOut, dependencies=[Depends(require_permissions("contracts.create"))])
def create_contract_endpoint(data: ContractCreate, db: Session = Depends(get_db)):
    try:
        c = create_contract(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ContractOut(**c.__dict__)


@router.put("/{contract_id}", response_model=ContractOut, dependencies=[Depends(require_permissions("contracts.update"))])
def update_contract_endpoint(contract_id: int, data: ContractUpdate, db: Session = Depends(get_db)):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    try:
        c = update_contract(db, c, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ContractOut(**c.__dict__)


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return ContractOut(**c.__dict__)

