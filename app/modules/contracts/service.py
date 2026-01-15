"""
Arquivo: app/modules/contracts/service.py

Responsabilidade:
Regras de negócio para criação e atualização de contratos, validações básicas
de consistência (cliente, plano, datas).

Integrações:
- modules.contracts.models
- modules.clients.models
- modules.plans.models
"""

from sqlalchemy.orm import Session
from .models import Contract
from ..clients.models import Client
from ..plans.models import Plan
from .schemas import ContractCreate, ContractUpdate


def create_contract(db: Session, data: ContractCreate) -> Contract:
    client = db.query(Client).filter(Client.id == data.client_id).first()
    plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
    if not client or not client.is_active:
        raise ValueError("Invalid or inactive client")
    if not plan or not plan.is_active:
        raise ValueError("Invalid or inactive plan")
    if data.end_date and data.end_date < data.start_date:
        raise ValueError("end_date must be >= start_date")
    contract = Contract(**data.dict())
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def update_contract(db: Session, contract: Contract, data: ContractUpdate) -> Contract:
    if data.end_date and contract.start_date and data.end_date < contract.start_date:
        raise ValueError("end_date must be >= start_date")
    for field, value in data.dict(exclude_none=True).items():
        setattr(contract, field, value)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract

