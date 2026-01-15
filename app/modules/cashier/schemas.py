"""
Arquivo: app/modules/cashier/schemas.py

Responsabilidade:
Esquemas Pydantic para Caixa.

Integrações:
- modules.cashier.models
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CashRegisterOpen(BaseModel):
    opening_balance: float = 0.0
    opening_notes: Optional[str] = None


class CashRegisterClose(BaseModel):
    closing_balance: float
    closing_notes: Optional[str] = None


class CashRegisterOut(BaseModel):
    id: int
    user_id: int
    opened_at: datetime
    closed_at: Optional[datetime]
    opening_balance: float
    closing_balance: Optional[float]
    expected_balance: Optional[float]
    difference: Optional[float]
    status: str
    opening_notes: Optional[str]
    closing_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CashMovementCreate(BaseModel):
    cash_register_id: int
    type: str  # in, out
    category: str  # payment, withdrawal, transfer, other
    amount: float
    title_id: Optional[int] = None
    client_id: Optional[int] = None
    payment_method: Optional[str] = None
    description: str
    document_number: Optional[str] = None


class CashMovementOut(BaseModel):
    id: int
    cash_register_id: int
    type: str
    category: str
    amount: float
    title_id: Optional[int]
    client_id: Optional[int]
    payment_method: Optional[str]
    description: str
    document_number: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CashRegisterSummary(BaseModel):
    cash_register_id: int
    total_in: float
    total_out: float
    net_balance: float
    movements_count: int
    movements_by_category: dict
    movements_by_payment_method: dict


class CashRegisterReport(BaseModel):
    cash_register: CashRegisterOut
    summary: CashRegisterSummary
    movements: List[CashMovementOut]
