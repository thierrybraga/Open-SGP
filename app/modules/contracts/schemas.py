"""
Arquivo: app/modules/contracts/schemas.py

Responsabilidade:
Esquemas Pydantic para contratos, com filtros e payloads de criação/atualização.

Integrações:
- modules.contracts.models
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel


class ContractBase(BaseModel):
    client_id: int
    plan_id: int
    status: str
    start_date: date
    end_date: Optional[date] = None
    installation_address: str
    billing_day: int = 10
    suspend_on_arrears: bool = True
    loyalty_months: int = 0
    price_override: Optional[float] = None


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    status: Optional[str] = None
    end_date: Optional[date] = None
    installation_address: Optional[str] = None
    billing_day: Optional[int] = None
    suspend_on_arrears: Optional[bool] = None
    loyalty_months: Optional[int] = None
    price_override: Optional[float] = None


class ContractOut(ContractBase):
    id: int

    class Config:
        from_attributes = True

