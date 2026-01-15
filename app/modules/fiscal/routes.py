"""
Arquivo: app/modules/fiscal/routes.py

Responsabilidade:
Rotas REST para fiscal: criar, emitir, cancelar e listar invoices.

Integrações:
- core.dependencies
- modules.fiscal.service
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Invoice, ServicePlanDetail, TVTelephonyGateway
from .schemas import (
    InvoiceCreate, InvoiceIssue, InvoiceCancel, InvoiceOut, ICMS115Request, ICMS115Out,
    BatchInvoiceCreate, BatchInvoiceResult,
    DebitNoteCreate, DebitNoteOut,
    ServicePlanDetailCreate, ServicePlanDetailUpdate, ServicePlanDetailOut,
    TVTelephonyGatewayCreate, TVTelephonyGatewayUpdate, TVTelephonyGatewayOut,
    ReportNF2122Request, ReportNF2122Out
)
from .service import (
    create_invoice, issue_invoice, cancel_invoice, generate_icms115, sign_invoice_a1, send_to_sefaz, create_invoices_batch,
    create_debit_note,
    create_service_plan_detail, update_service_plan_detail, get_plan_fiscal_config,
    create_tv_telephony_gateway, update_tv_telephony_gateway, test_tv_telephony_gateway,
    generate_report_nf_2122
)


router = APIRouter()


@router.get("/invoices", response_model=List[InvoiceOut])
def list_invoices(
    status_: Optional[str] = Query(default=None, alias="status"),
    contract_id: Optional[int] = Query(default=None),
    number: Optional[str] = Query(default=None),
    issued_from: Optional[date] = Query(default=None),
    issued_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Invoice)
    if status_:
        q = q.filter(Invoice.status == status_)
    if contract_id:
        q = q.filter(Invoice.contract_id == contract_id)
    if number:
        q = q.filter(Invoice.number == number)
    if issued_from:
        q = q.filter(Invoice.issue_date >= issued_from)
    if issued_to:
        q = q.filter(Invoice.issue_date <= issued_to)
    items = q.all()
    return [InvoiceOut(**i.__dict__) for i in items]


@router.post("/invoices", response_model=InvoiceOut, dependencies=[Depends(require_permissions("fiscal.invoices.create"))])
def create_invoice_endpoint(data: InvoiceCreate, db: Session = Depends(get_db)):
    try:
        inv = create_invoice(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return InvoiceOut(**inv.__dict__)


@router.post("/invoices/{invoice_id}/issue", response_model=InvoiceOut, dependencies=[Depends(require_permissions("fiscal.invoices.issue"))])
def issue_invoice_endpoint(invoice_id: int, payload: InvoiceIssue, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    inv = issue_invoice(db, inv, payload)
    return InvoiceOut(**inv.__dict__)


@router.post("/invoices/{invoice_id}/cancel", response_model=InvoiceOut, dependencies=[Depends(require_permissions("fiscal.invoices.cancel"))])
def cancel_invoice_endpoint(invoice_id: int, payload: InvoiceCancel, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    try:
        inv = cancel_invoice(db, inv, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return InvoiceOut(**inv.__dict__)


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return InvoiceOut(**inv.__dict__)


@router.post("/icms115", response_model=ICMS115Out)
def generate_icms115_endpoint(filters: ICMS115Request, db: Session = Depends(get_db)):
    out = generate_icms115(db, filters)
    return out


@router.post("/invoices/{invoice_id}/sign-a1", response_model=InvoiceOut, dependencies=[Depends(require_permissions("fiscal.invoices.issue"))])
def sign_a1_endpoint(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    inv = sign_invoice_a1(inv)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return InvoiceOut(**inv.__dict__)


@router.post("/invoices/{invoice_id}/send-sefaz", response_model=InvoiceOut, dependencies=[Depends(require_permissions("fiscal.invoices.issue"))])
def send_sefaz_endpoint(invoice_id: int, force: bool = False, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    inv = send_to_sefaz(inv, force=force)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return InvoiceOut(**inv.__dict__)


# ===== BATCH GENERATION =====

@router.post("/invoices/batch", response_model=BatchInvoiceResult, dependencies=[Depends(require_permissions("fiscal.invoices.create"))])
def create_invoices_batch_endpoint(data: BatchInvoiceCreate, db: Session = Depends(get_db)):
    """
    Cria notas fiscais em lote a partir de uma lista de títulos.
    """
    result = create_invoices_batch(db, data)
    return BatchInvoiceResult(**result)


# ===== DEBIT NOTE =====

@router.post("/debit-notes", response_model=DebitNoteOut, dependencies=[Depends(require_permissions("fiscal.debit_notes.create"))])
def create_debit_note_endpoint(data: DebitNoteCreate, db: Session = Depends(get_db)):
    """
    Cria nota de débito.
    """
    try:
        debit_note = create_debit_note(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return DebitNoteOut(**debit_note.__dict__)


@router.get("/debit-notes", response_model=List[DebitNoteOut])
def list_debit_notes(
    contract_id: Optional[int] = Query(default=None),
    reference_invoice_id: Optional[int] = Query(default=None),
    status_: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    Lista notas de débito.
    """
    q = db.query(Invoice).filter(Invoice.invoice_type == "debit_note")

    if contract_id:
        q = q.filter(Invoice.contract_id == contract_id)
    if reference_invoice_id:
        q = q.filter(Invoice.reference_invoice_id == reference_invoice_id)
    if status_:
        q = q.filter(Invoice.status == status_)

    items = q.order_by(Invoice.created_at.desc()).all()
    return [DebitNoteOut(**i.__dict__) for i in items]


@router.get("/debit-notes/{debit_note_id}", response_model=DebitNoteOut)
def get_debit_note(debit_note_id: int, db: Session = Depends(get_db)):
    """
    Busca nota de débito por ID.
    """
    debit_note = db.query(Invoice).filter(
        Invoice.id == debit_note_id,
        Invoice.invoice_type == "debit_note"
    ).first()

    if not debit_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debit note not found")

    return DebitNoteOut(**debit_note.__dict__)


# ===== SERVICE PLAN DETAIL =====

@router.get("/plan-details", response_model=List[ServicePlanDetailOut])
def list_plan_details(
    plan_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista configurações fiscais de planos.
    """
    q = db.query(ServicePlanDetail)

    if plan_id:
        q = q.filter(ServicePlanDetail.plan_id == plan_id)

    items = q.all()
    return [ServicePlanDetailOut(**d.__dict__) for d in items]


@router.post("/plan-details", response_model=ServicePlanDetailOut, dependencies=[Depends(require_permissions("fiscal.plan_details.create"))])
def create_plan_detail_endpoint(data: ServicePlanDetailCreate, db: Session = Depends(get_db)):
    """
    Cria configuração fiscal para plano.
    """
    try:
        detail = create_service_plan_detail(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ServicePlanDetailOut(**detail.__dict__)


@router.get("/plan-details/{detail_id}", response_model=ServicePlanDetailOut)
def get_plan_detail(detail_id: int, db: Session = Depends(get_db)):
    """
    Busca configuração fiscal por ID.
    """
    detail = db.query(ServicePlanDetail).filter(ServicePlanDetail.id == detail_id).first()

    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan detail not found")

    return ServicePlanDetailOut(**detail.__dict__)


@router.put("/plan-details/{detail_id}", response_model=ServicePlanDetailOut, dependencies=[Depends(require_permissions("fiscal.plan_details.update"))])
def update_plan_detail_endpoint(
    detail_id: int,
    data: ServicePlanDetailUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza configuração fiscal de plano.
    """
    detail = db.query(ServicePlanDetail).filter(ServicePlanDetail.id == detail_id).first()

    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan detail not found")

    detail = update_service_plan_detail(db, detail, data)
    return ServicePlanDetailOut(**detail.__dict__)


@router.delete("/plan-details/{detail_id}", dependencies=[Depends(require_permissions("fiscal.plan_details.delete"))])
def delete_plan_detail(detail_id: int, db: Session = Depends(get_db)):
    """
    Remove configuração fiscal de plano.
    """
    detail = db.query(ServicePlanDetail).filter(ServicePlanDetail.id == detail_id).first()

    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan detail not found")

    db.delete(detail)
    db.commit()

    return {"message": "Plan detail deleted successfully"}


@router.get("/plan-details/plan/{plan_id}/config")
def get_plan_config(plan_id: int, db: Session = Depends(get_db)):
    """
    Retorna configuração fiscal de um plano (para uso em geração de NF).
    """
    config = get_plan_fiscal_config(db, plan_id)
    return config


# ===== TV/TELEPHONY GATEWAY =====

@router.get("/tv-telephony-gateways", response_model=List[TVTelephonyGatewayOut])
def list_tv_telephony_gateways(
    gateway_type: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista gateways de TV/Telefonia.
    """
    q = db.query(TVTelephonyGateway)

    if gateway_type:
        q = q.filter(TVTelephonyGateway.gateway_type == gateway_type)
    if is_active is not None:
        q = q.filter(TVTelephonyGateway.is_active == is_active)

    items = q.order_by(TVTelephonyGateway.created_at.desc()).all()
    return [TVTelephonyGatewayOut(**g.__dict__) for g in items]


@router.post("/tv-telephony-gateways", response_model=TVTelephonyGatewayOut, dependencies=[Depends(require_permissions("fiscal.tv_telephony_gateways.create"))])
def create_tv_telephony_gateway_endpoint(data: TVTelephonyGatewayCreate, db: Session = Depends(get_db)):
    """
    Cria gateway de TV/Telefonia.
    """
    gateway = create_tv_telephony_gateway(db, data)
    return TVTelephonyGatewayOut(**gateway.__dict__)


@router.get("/tv-telephony-gateways/{gateway_id}", response_model=TVTelephonyGatewayOut)
def get_tv_telephony_gateway(gateway_id: int, db: Session = Depends(get_db)):
    """
    Busca gateway por ID.
    """
    gateway = db.query(TVTelephonyGateway).filter(TVTelephonyGateway.id == gateway_id).first()

    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")

    return TVTelephonyGatewayOut(**gateway.__dict__)


@router.put("/tv-telephony-gateways/{gateway_id}", response_model=TVTelephonyGatewayOut, dependencies=[Depends(require_permissions("fiscal.tv_telephony_gateways.update"))])
def update_tv_telephony_gateway_endpoint(
    gateway_id: int,
    data: TVTelephonyGatewayUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza gateway.
    """
    gateway = db.query(TVTelephonyGateway).filter(TVTelephonyGateway.id == gateway_id).first()

    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")

    gateway = update_tv_telephony_gateway(db, gateway, data)
    return TVTelephonyGatewayOut(**gateway.__dict__)


@router.delete("/tv-telephony-gateways/{gateway_id}", dependencies=[Depends(require_permissions("fiscal.tv_telephony_gateways.delete"))])
def delete_tv_telephony_gateway(gateway_id: int, db: Session = Depends(get_db)):
    """
    Remove gateway.
    """
    gateway = db.query(TVTelephonyGateway).filter(TVTelephonyGateway.id == gateway_id).first()

    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")

    db.delete(gateway)
    db.commit()

    return {"message": "Gateway deleted successfully"}


@router.post("/tv-telephony-gateways/{gateway_id}/test", dependencies=[Depends(require_permissions("fiscal.tv_telephony_gateways.test"))])
def test_tv_telephony_gateway_endpoint(gateway_id: int, db: Session = Depends(get_db)):
    """
    Testa conexão com gateway.
    """
    try:
        result = test_tv_telephony_gateway(db, gateway_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== REPORT NF 21/22 =====

@router.post("/reports/nf-2122", response_model=ReportNF2122Out)
def generate_report_nf_2122_endpoint(filters: ReportNF2122Request, db: Session = Depends(get_db)):
    """
    Gera relatório de notas fiscais modelo 21/22.
    """
    result = generate_report_nf_2122(db, filters)
    return ReportNF2122Out(**result)
