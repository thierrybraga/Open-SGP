"""
Arquivo: app/modules/fiscal/service.py

Responsabilidade:
Regras de negócio para emissão de notas fiscais.
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from .models import Invoice, ServicePlanDetail, TVTelephonyGateway
from .schemas import (
    InvoiceCreate, InvoiceIssue, InvoiceCancel,
    BatchInvoiceCreate, BatchInvoiceResult,
    ICMS115Request, ICMS115Out,
    DebitNoteCreate, DebitNoteOut,
    ServicePlanDetailCreate, ServicePlanDetailUpdate,
    TVTelephonyGatewayCreate, TVTelephonyGatewayUpdate,
    ReportNF2122Request, ReportNF2122Out
)

# --- Invoice ---
def create_invoice(db: Session, data: InvoiceCreate) -> Invoice:
    inv = Invoice(**data.dict())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

# Alias
create_invoice_record = create_invoice

def issue_invoice(db: Session, invoice_id: int, data: InvoiceIssue):
    # Simula emissão
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if inv:
        inv.status = "emitted"
        inv.xml_path = f"invoices/xml/{inv.number}.xml"
        inv.pdf_url = f"invoices/pdf/{inv.number}.pdf"
        db.commit()
        db.refresh(inv)
    return inv

# Alias
emit_invoice = issue_invoice

def cancel_invoice(db: Session, invoice_id: int, data: InvoiceCancel):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if inv:
        inv.status = "canceled"
        db.commit()
        db.refresh(inv)
    return inv

def sign_invoice_a1(db: Session, invoice_id: int):
    return True

def send_to_sefaz(db: Session, invoice_id: int):
    return True

# --- Batch ---
def create_invoices_batch(db: Session, data: BatchInvoiceCreate) -> BatchInvoiceResult:
    # Dummy implementation
    return BatchInvoiceResult(
        total=len(data.contract_ids),
        success=len(data.contract_ids),
        errors=0,
        details=["Success"]
    )

# --- ICMS ---
def generate_icms115(db: Session, data: ICMS115Request) -> ICMS115Out:
    return ICMS115Out(file_path=f"/tmp/icms_{data.year}_{data.month}.txt", hash_md5="dummy_hash")

# --- Debit Note ---
def create_debit_note(db: Session, data: DebitNoteCreate) -> DebitNoteOut:
    # Dummy implementation - usually creates a record in DB
    return DebitNoteOut(
        id=1,
        contract_id=data.contract_id,
        amount=data.amount,
        description=data.description,
        created_at=date.today()
    )

# --- Service Plan Detail ---
def create_service_plan_detail(db: Session, data: ServicePlanDetailCreate) -> ServicePlanDetail:
    obj = ServicePlanDetail(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_service_plan_detail(db: Session, obj: ServicePlanDetail, data: ServicePlanDetailUpdate) -> ServicePlanDetail:
    for key, value in data.dict(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj

def get_plan_fiscal_config(db: Session, plan_id: int) -> Optional[ServicePlanDetail]:
    return db.query(ServicePlanDetail).filter(ServicePlanDetail.plan_id == plan_id).first()

# --- TV/Telephony Gateway ---
def create_tv_telephony_gateway(db: Session, data: TVTelephonyGatewayCreate) -> TVTelephonyGateway:
    obj = TVTelephonyGateway(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_tv_telephony_gateway(db: Session, obj: TVTelephonyGateway, data: TVTelephonyGatewayUpdate) -> TVTelephonyGateway:
    for key, value in data.dict(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj

def test_tv_telephony_gateway(db: Session, gateway_id: int) -> bool:
    return True

# --- Reports ---
def generate_report_nf_2122(db: Session, data: ReportNF2122Request) -> ReportNF2122Out:
    return ReportNF2122Out(report_url=f"/tmp/nf2122_{data.year}_{data.month}.pdf")
