"""
Arquivo: app/modules/administration/finance/schemas.py

Responsabilidade:
Esquemas Pydantic para cadastros financeiros.

Integrações:
- modules.administration.finance.models
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class CompanyCreate(BaseModel):
    name: str
    legal_name: str
    document: str
    email: EmailStr
    phone: str
    is_active: bool = True


class CompanyOut(BaseModel):
    id: int
    name: str
    legal_name: str
    document: str
    email: EmailStr
    phone: str
    is_active: bool

    class Config:
        from_attributes = True


class CarrierCreate(BaseModel):
    name: str
    bank_code: str
    agency: str
    account: str
    wallet: str
    is_active: bool = True


class CarrierOut(CarrierCreate):
    id: int

    class Config:
        from_attributes = True


class ReceiptPointCreate(BaseModel):
    name: str
    description: str
    company_id: int


class ReceiptPointOut(ReceiptPointCreate):
    id: int

    class Config:
        from_attributes = True


class FinancialParameterCreate(BaseModel):
    company_id: int
    default_carrier_id: Optional[int] = None
    fine_percent: float = 2.0
    interest_percent: float = 1.0
    send_email_on_issue: bool = False


class FinancialParameterOut(FinancialParameterCreate):
    id: int

    class Config:
        from_attributes = True
