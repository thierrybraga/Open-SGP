"""
Arquivo: app/modules/billing/routes.py

Responsabilidade:
Rotas REST para financeiro: títulos, boletos, remessa/retorno CNAB e promessas.

Integrações:
- core.dependencies
- modules.billing.service
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from fastapi.responses import Response

from ...core.dependencies import get_db, require_permissions
from .models import Title, PaymentPromise, Remittance, ReturnFile
from .models import TitleAdjustment
from .schemas import (
    TitleCreate,
    TitleUpdate,
    TitleOut,
    GenerateBoletoOut,
    RemittanceCreate,
    RemittanceOut,
    RemittanceFileOut,
    ReturnCreate,
    ReturnOut,
    PaymentPromiseCreate,
    PaymentPromiseOut,
    CarneCreate,
    AdjustmentCreate,
    AdjustmentOut,
    BatchTitleCreate,
    BatchTitleOut,
    BatchCarneCreate,
    BatchCarneOut,
    BatchBoletoGenerate,
    BatchBoletoOut,
)
from .service import (
    create_title,
    update_title,
    generate_boleto,
    register_payment,
    create_remittance,
    process_return,
    create_promise,
    generate_carne,
    generate_remittance_file,
    generate_remittance_file_for_default_carrier,
    create_adjustment,
    calculate_title_effective_amount,
    create_titles_batch,
    generate_carnes_batch,
    generate_boletos_batch,
)


router = APIRouter()


@router.get("/titles", response_model=List[TitleOut])
def list_titles(
    status_: Optional[str] = Query(default=None, alias="status"),
    contract_id: Optional[int] = Query(default=None),
    due_from: Optional[date] = Query(default=None),
    due_to: Optional[date] = Query(default=None),
    overdue: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Title)
    if status_:
        q = q.filter(Title.status == status_)
    if contract_id:
        q = q.filter(Title.contract_id == contract_id)
    if due_from:
        q = q.filter(Title.due_date >= due_from)
    if due_to:
        q = q.filter(Title.due_date <= due_to)
    if overdue:
        today = date.today()
        q = q.filter(Title.due_date < today, Title.status == "open")
    items = q.all()
    return [TitleOut(**t.__dict__) for t in items]


@router.post("/titles", response_model=TitleOut, dependencies=[Depends(require_permissions("billing.titles.create"))])
def create_title_endpoint(data: TitleCreate, db: Session = Depends(get_db)):
    try:
        t = create_title(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return TitleOut(**t.__dict__)


@router.put("/titles/{title_id}", response_model=TitleOut, dependencies=[Depends(require_permissions("billing.titles.update"))])
def update_title_endpoint(title_id: int, data: TitleUpdate, db: Session = Depends(get_db)):
    t = db.query(Title).filter(Title.id == title_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")
    t = update_title(db, t, data)
    return TitleOut(**t.__dict__)


@router.post("/titles/{title_id}/generate_boleto", response_model=GenerateBoletoOut, dependencies=[Depends(require_permissions("billing.boletos.generate"))])
def generate_boleto_endpoint(title_id: int, db: Session = Depends(get_db)):
    t = db.query(Title).filter(Title.id == title_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")
    t = generate_boleto(db, t)
    return GenerateBoletoOut(payment_slip_url=t.payment_slip_url or "", bar_code=t.bar_code or "")


@router.post("/titles/{title_id}/pay", response_model=TitleOut, dependencies=[Depends(require_permissions("billing.titles.update"))])
def pay_title_endpoint(title_id: int, amount: float, method: str = "boleto", db: Session = Depends(get_db)):
    t = db.query(Title).filter(Title.id == title_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")
    t = register_payment(db, t, amount, method)
    return TitleOut(**t.__dict__)


@router.post("/cnab/remit", response_model=RemittanceOut, dependencies=[Depends(require_permissions("billing.cnab.remit"))])
def create_remittance_endpoint(data: RemittanceCreate, db: Session = Depends(get_db)):
    rem = create_remittance(db, data)
    return RemittanceOut(**rem.__dict__)


@router.post("/cnab/return", response_model=ReturnOut, dependencies=[Depends(require_permissions("billing.cnab.return"))])
def process_return_endpoint(data: ReturnCreate, db: Session = Depends(get_db)):
    rf = process_return(db, data)
    return ReturnOut(**rf.__dict__)


@router.get("/cnab/remit/file", response_model=RemittanceFileOut, dependencies=[Depends(require_permissions("billing.cnab.remit"))])
def generate_remittance_file_endpoint(
    bank_code: Optional[str] = Query(default=None),
    layout: Optional[str] = Query(default=None),
    due_from: Optional[date] = Query(default=None),
    due_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    if bank_code:
        content = generate_remittance_file(db, bank_code, due_from, due_to, layout)
    else:
        content = generate_remittance_file_for_default_carrier(db, due_from, due_to)
    return RemittanceFileOut(content=content)


@router.get("/promises", response_model=List[PaymentPromiseOut])
def list_promises(client_id: Optional[int] = None, contract_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(PaymentPromise)
    if client_id:
        q = q.filter(PaymentPromise.client_id == client_id)
    if contract_id:
        q = q.filter(PaymentPromise.contract_id == contract_id)
    items = q.all()
    return [PaymentPromiseOut(**p.__dict__) for p in items]


@router.post("/promises", response_model=PaymentPromiseOut, dependencies=[Depends(require_permissions("billing.promises.create"))])
def create_promise_endpoint(data: PaymentPromiseCreate, db: Session = Depends(get_db)):
    p = create_promise(db, data)
    return PaymentPromiseOut(**p.__dict__)


@router.post("/carne/generate", dependencies=[Depends(require_permissions("billing.titles.create"))])
def generate_carne_endpoint(data: CarneCreate, db: Session = Depends(get_db)):
    try:
        res = generate_carne(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return res


@router.get("/titles/{title_id}/adjustments", response_model=List[AdjustmentOut])
def list_adjustments(title_id: int, db: Session = Depends(get_db)):
    items = db.query(TitleAdjustment).filter(TitleAdjustment.title_id == title_id).all()
    return [AdjustmentOut(**a.__dict__) for a in items]


@router.post(
    "/titles/{title_id}/adjustments",
    response_model=AdjustmentOut,
    dependencies=[Depends(require_permissions("billing.titles.update"))],
)
def create_adjustment_endpoint(title_id: int, data: AdjustmentCreate, db: Session = Depends(get_db)):
    try:
        a = create_adjustment(db, title_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return AdjustmentOut(**a.__dict__)


@router.get("/titles/{title_id}/effective-amount")
def get_effective_amount(title_id: int, db: Session = Depends(get_db)):
    try:
        val = calculate_title_effective_amount(db, title_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"title_id": title_id, "effective_amount": val}


@router.post("/titles/batch", response_model=BatchTitleOut, dependencies=[Depends(require_permissions("billing.titles.create"))])
def create_titles_batch_endpoint(data: BatchTitleCreate, db: Session = Depends(get_db)):
    """
    Cria títulos em lote para múltiplos contratos.
    Útil para geração mensal de cobranças.
    """
    result = create_titles_batch(db, data)
    return result


@router.post("/carne/batch", response_model=BatchCarneOut, dependencies=[Depends(require_permissions("billing.titles.create"))])
def generate_carnes_batch_endpoint(data: BatchCarneCreate, db: Session = Depends(get_db)):
    """
    Gera carnês em lote para múltiplos contratos.
    Cria vários meses de títulos de uma vez.
    """
    result = generate_carnes_batch(db, data)
    return result


@router.post("/boletos/batch", response_model=BatchBoletoOut, dependencies=[Depends(require_permissions("billing.boletos.generate"))])
def generate_boletos_batch_endpoint(data: BatchBoletoGenerate, db: Session = Depends(get_db)):
    """
    Gera boletos em lote para múltiplos títulos.
    Útil para gerar todos os boletos de uma remessa.
    """
    result = generate_boletos_batch(db, data)
    return result


# ===== PDF GENERATION =====

@router.get("/carne/{contract_id}/pdf")
def download_carne_pdf(
    contract_id: int,
    db: Session = Depends(get_db)
):
    """
    Gera e retorna PDF do carnê de um contrato.
    """
    from ..contracts.models import Contract
    from .pdf_generator import generate_carne_pdf

    # Buscar contrato
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    # Buscar títulos do contrato
    titles = db.query(Title).filter(
        Title.contract_id == contract_id
    ).order_by(Title.due_date).all()

    if not titles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No titles found for this contract")

    # Gerar PDF
    pdf_bytes = generate_carne_pdf(
        titles,
        contract.client.name if contract.client else "Cliente",
        contract_id
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=carne_contract_{contract_id}.pdf"}
    )


@router.post("/carne/batch/pdf")
def download_batch_carne_pdf(
    contract_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Gera PDF com múltiplos carnês em um único arquivo.
    """
    from ..contracts.models import Contract
    from .pdf_generator import generate_batch_carne_pdf

    carnes_data = []

    for contract_id in contract_ids:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            continue

        titles = db.query(Title).filter(
            Title.contract_id == contract_id
        ).order_by(Title.due_date).all()

        if titles:
            carnes_data.append({
                'titles': titles,
                'client_name': contract.client.name if contract.client else "Cliente",
                'contract_id': contract_id
            })

    if not carnes_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data found for any contract")

    # Gerar PDF consolidado
    pdf_bytes = generate_batch_carne_pdf(carnes_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=carnes_batch.pdf"}
    )


@router.get("/boleto/{title_id}/pdf")
def download_boleto_pdf(
    title_id: int,
    db: Session = Depends(get_db)
):
    """
    Gera e retorna PDF do boleto de um título.
    """
    from ..contracts.models import Contract
    from ..administration.finance.models import Company
    from .pdf_generator import generate_boleto_pdf

    # Buscar título
    title = db.query(Title).filter(Title.id == title_id).first()
    if not title:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")

    # Buscar contrato e cliente
    contract = db.query(Contract).filter(Contract.id == title.contract_id).first()
    if not contract or not contract.client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract or client not found")

    # Buscar empresa
    company = db.query(Company).first()
    company_data = {
        'name': company.name if company else 'Empresa',
        'document': company.document if company else ''
    }

    client_data = {
        'name': contract.client.name,
        'document': contract.client.document
    }

    # Gerar PDF
    pdf_bytes = generate_boleto_pdf(title, client_data, company_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=boleto_{title_id}.pdf"}
    )
