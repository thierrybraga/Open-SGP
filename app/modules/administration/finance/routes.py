"""
Arquivo: app/modules/administration/finance/routes.py

Responsabilidade:
Rotas REST para cadastros financeiros: Empresas, Portadores, Pontos de Recebimento,
Parâmetros Financeiros.

Integrações:
- core.dependencies
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import Company, Carrier, ReceiptPoint, FinancialParameter
from .schemas import (
    CompanyCreate,
    CompanyOut,
    CarrierCreate,
    CarrierOut,
    ReceiptPointCreate,
    ReceiptPointOut,
    FinancialParameterCreate,
    FinancialParameterOut,
)


router = APIRouter()


@router.get("/companies", response_model=List[CompanyOut])
def list_companies(db: Session = Depends(get_db)):
    items = db.query(Company).all()
    return [CompanyOut(**c.__dict__) for c in items]


@router.post("/companies", response_model=CompanyOut, dependencies=[Depends(require_permissions("admin.finance.companies.create"))])
def create_company_endpoint(data: CompanyCreate, db: Session = Depends(get_db)):
    if db.query(Company).filter(Company.document == data.document).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company already exists")
    c = Company(**data.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return CompanyOut(**c.__dict__)


@router.get("/carriers", response_model=List[CarrierOut])
def list_carriers(db: Session = Depends(get_db)):
    items = db.query(Carrier).all()
    return [CarrierOut(**c.__dict__) for c in items]


@router.post("/carriers", response_model=CarrierOut, dependencies=[Depends(require_permissions("admin.finance.carriers.create"))])
def create_carrier_endpoint(data: CarrierCreate, db: Session = Depends(get_db)):
    c = Carrier(**data.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return CarrierOut(**c.__dict__)


@router.get("/receipt-points", response_model=List[ReceiptPointOut])
def list_receipt_points(db: Session = Depends(get_db)):
    items = db.query(ReceiptPoint).all()
    return [ReceiptPointOut(**r.__dict__) for r in items]


@router.post("/receipt-points", response_model=ReceiptPointOut, dependencies=[Depends(require_permissions("admin.finance.receipts.create"))])
def create_receipt_point_endpoint(data: ReceiptPointCreate, db: Session = Depends(get_db)):
    r = ReceiptPoint(**data.dict())
    db.add(r)
    db.commit()
    db.refresh(r)
    return ReceiptPointOut(**r.__dict__)


@router.get("/parameters", response_model=List[FinancialParameterOut])
def list_parameters(db: Session = Depends(get_db)):
    items = db.query(FinancialParameter).all()
    return [FinancialParameterOut(**p.__dict__) for p in items]


@router.post("/parameters", response_model=FinancialParameterOut, dependencies=[Depends(require_permissions("admin.finance.parameters.create"))])
def create_parameter_endpoint(data: FinancialParameterCreate, db: Session = Depends(get_db)):
    p = FinancialParameter(**data.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return FinancialParameterOut(**p.__dict__)
