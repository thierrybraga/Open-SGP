"""
Arquivo: app/modules/fiscal/schemas.py

Responsabilidade:
Schemas Pydantic para validação de dados fiscais.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# --- Invoice ---
class InvoiceBase(BaseModel):
    contract_id: int
    title_id: Optional[int] = None
    number: str
    series: str
    status: str
    issue_date: Optional[date] = None
    total_amount: float
    service_description: str
    municipality_code: str
    taxation_code: str
    invoice_type: str = "service"
    debit_reason: Optional[str] = None
    reference_invoice_id: Optional[int] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    xml_path: Optional[str] = None
    pdf_url: Optional[str] = None

    class Config:
        from_attributes = True

# Alias for routes
InvoiceOut = InvoiceResponse

class InvoiceIssue(BaseModel):
    pass # Placeholder for issue parameters

class InvoiceCancel(BaseModel):
    reason: str

# --- Batch ---
class BatchInvoiceCreate(BaseModel):
    contract_ids: List[int]
    issue_date: date

class BatchInvoiceResult(BaseModel):
    total: int
    success: int
    errors: int
    details: List[str]

# --- ICMS ---
class ICMS115Request(BaseModel):
    month: int
    year: int

class ICMS115Out(BaseModel):
    file_path: str
    hash_md5: str

# --- Debit Note ---
class DebitNoteCreate(BaseModel):
    contract_id: int
    amount: float
    description: str

class DebitNoteOut(BaseModel):
    id: int
    contract_id: int
    amount: float
    description: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Service Plan Detail ---
class ServicePlanDetailBase(BaseModel):
    plan_id: int
    service_code: str
    cnae_code: Optional[str] = None
    taxation_code: str
    fiscal_description: str
    iss_rate: float = 0.0
    cofins_rate: float = 0.0
    pis_rate: float = 0.0
    csll_rate: float = 0.0
    irpj_rate: float = 0.0
    iss_retention: bool = False
    municipality_code: str
    notes: Optional[str] = None

class ServicePlanDetailCreate(ServicePlanDetailBase):
    pass

class ServicePlanDetailUpdate(ServicePlanDetailBase):
    pass

class ServicePlanDetailResponse(ServicePlanDetailBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Alias
ServicePlanDetailOut = ServicePlanDetailResponse

# --- TV/Telephony Gateway ---
class TVTelephonyGatewayCreate(BaseModel):
    name: str
    url: str
    username: str
    password: str

class TVTelephonyGatewayUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class TVTelephonyGatewayOut(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Reports ---
class ReportNF2122Request(BaseModel):
    month: int
    year: int

class ReportNF2122Out(BaseModel):
    report_url: str
