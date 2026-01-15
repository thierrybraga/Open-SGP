"""
Arquivo: app/modules/billing/schemas.py

Responsabilidade:
Esquemas Pydantic para Títulos, Boletos, Remessas CNAB, Retornos e Promessas.

Integrações:
- modules.billing.models
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class TitleCreate(BaseModel):
    contract_id: int
    issue_date: date
    due_date: date
    amount: float
    status: str = "open"
    fine_percent: float = 2.0
    interest_percent: float = 1.0
    bank_code: str = "341"
    document_number: str
    our_number: str


class TitleUpdate(BaseModel):
    due_date: Optional[date] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    fine_percent: Optional[float] = None
    interest_percent: Optional[float] = None
    bank_code: Optional[str] = None
    payment_slip_url: Optional[str] = None
    bar_code: Optional[str] = None


class TitleOut(BaseModel):
    id: int
    contract_id: int
    issue_date: date
    due_date: date
    paid_date: Optional[date]
    amount: float
    status: str
    fine_percent: float
    interest_percent: float
    bank_code: str
    document_number: str
    our_number: str
    payment_slip_url: Optional[str]
    bar_code: Optional[str]

    class Config:
        from_attributes = True


class GenerateBoletoOut(BaseModel):
    payment_slip_url: str
    bar_code: str


class RemittanceCreate(BaseModel):
    file_name: str
    due_from: Optional[date] = None
    due_to: Optional[date] = None
    bank_code: Optional[str] = None
    layout: Optional[str] = None  # "240" or "400"


class RemittanceOut(BaseModel):
    id: int
    file_name: str
    generated_at: str
    total_titles: int
    status: str

    class Config:
        from_attributes = True


class RemittanceFileOut(BaseModel):
    content: str


class ReturnCreate(BaseModel):
    file_name: str
    items: List[dict]


class ReturnOut(BaseModel):
    id: int
    file_name: str
    processed_at: Optional[str]
    total_items: int

    class Config:
        from_attributes = True


class PaymentPromiseCreate(BaseModel):
    client_id: int
    contract_id: int
    title_id: Optional[int] = None
    promised_date: date
    amount: float
    notes: Optional[str] = None


class PaymentPromiseOut(BaseModel):
    id: int
    client_id: int
    contract_id: int
    title_id: Optional[int]
    promised_date: date
    amount: float
    status: str
    notes: Optional[str]

    class Config:
        from_attributes = True


class CarneCreate(BaseModel):
    contract_id: int
    start_month: int  # 1-12
    start_year: int
    months: int
    amount: Optional[float] = None


class CarneOut(BaseModel):
    contract_id: int
    titles_created: int
    first_due_date: date
    last_due_date: date


class AdjustmentCreate(BaseModel):
    type: str  # "increase" or "discount"
    amount: float
    reason: Optional[str] = None


class AdjustmentOut(BaseModel):
    id: int
    title_id: int
    type: str
    amount: float
    reason: Optional[str]

    class Config:
        from_attributes = True


class BatchTitleCreate(BaseModel):
    contract_ids: List[int]
    issue_date: date
    due_date: date
    amount: Optional[float] = None  # Se None, usa valor do plano
    status: str = "open"
    fine_percent: float = 2.0
    interest_percent: float = 1.0
    bank_code: str = "341"


class BatchTitleOut(BaseModel):
    titles_created: int
    contract_ids: List[int]
    errors: List[dict] = []


class BatchCarneCreate(BaseModel):
    contract_ids: List[int]
    start_month: int  # 1-12
    start_year: int
    months: int
    amount: Optional[float] = None  # Se None, usa valor do plano


class BatchCarneOut(BaseModel):
    carnes_created: int
    total_titles_created: int
    contract_ids: List[int]
    errors: List[dict] = []


class BatchBoletoGenerate(BaseModel):
    title_ids: List[int]


class BatchBoletoOut(BaseModel):
    boletos_generated: int
    title_ids: List[int]
    errors: List[dict] = []
