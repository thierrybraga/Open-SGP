"""
Arquivo: app/modules/contract_templates/routes.py

Responsabilidade:
Rotas REST para Templates de Contrato e Aditivos.

Integrações:
- core.dependencies
- modules.contract_templates.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions, get_current_user
from .models import ContractTemplate, ContractAddendum
from .schemas import (
    ContractTemplateCreate,
    ContractTemplateUpdate,
    ContractTemplateOut,
    ContractAddendumCreate,
    ContractAddendumUpdate,
    ContractAddendumOut,
    GenerateContractRequest,
    GenerateContractOut
)
from .service import create_template, update_template, generate_contract_from_template, create_addendum, update_addendum


router = APIRouter()


# ===== TEMPLATES =====

@router.get("/templates", response_model=List[ContractTemplateOut])
def list_templates(
    active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista templates de contrato.
    """
    q = db.query(ContractTemplate)
    if active is not None:
        q = q.filter(ContractTemplate.is_active == active)

    items = q.order_by(ContractTemplate.created_at.desc()).all()
    return [ContractTemplateOut(**t.__dict__) for t in items]


@router.post("/templates", response_model=ContractTemplateOut, dependencies=[Depends(require_permissions("contracts.templates.create"))])
def create_template_endpoint(
    data: ContractTemplateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cria novo template de contrato.
    """
    t = create_template(db, data, user_id=current_user.id)
    return ContractTemplateOut(**t.__dict__)


@router.get("/templates/{template_id}", response_model=ContractTemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """
    Busca template por ID.
    """
    t = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    return ContractTemplateOut(**t.__dict__)


@router.put("/templates/{template_id}", response_model=ContractTemplateOut, dependencies=[Depends(require_permissions("contracts.templates.update"))])
def update_template_endpoint(
    template_id: int,
    data: ContractTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza template de contrato.
    """
    t = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    t = update_template(db, t, data)
    return ContractTemplateOut(**t.__dict__)


@router.delete("/templates/{template_id}", dependencies=[Depends(require_permissions("contracts.templates.delete"))])
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """
    Deleta template de contrato (soft delete via is_active).
    """
    t = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    t.is_active = False
    db.add(t)
    db.commit()

    return {"message": "Template deleted"}


@router.post("/generate", response_model=GenerateContractOut, dependencies=[Depends(require_permissions("contracts.generate"))])
def generate_contract_endpoint(
    data: GenerateContractRequest,
    db: Session = Depends(get_db)
):
    """
    Gera contrato a partir de template.
    """
    try:
        html = generate_contract_from_template(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return GenerateContractOut(contract_html=html, contract_pdf_url=None)


# ===== ADITIVOS =====

@router.get("/addendums", response_model=List[ContractAddendumOut])
def list_addendums(
    contract_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista aditivos contratuais.
    """
    q = db.query(ContractAddendum)
    if contract_id:
        q = q.filter(ContractAddendum.contract_id == contract_id)

    items = q.order_by(ContractAddendum.created_at.desc()).all()
    return [ContractAddendumOut(**a.__dict__) for a in items]


@router.post("/addendums", response_model=ContractAddendumOut, dependencies=[Depends(require_permissions("contracts.addendums.create"))])
def create_addendum_endpoint(
    data: ContractAddendumCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cria novo aditivo contratual.
    """
    try:
        a = create_addendum(db, data, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ContractAddendumOut(**a.__dict__)


@router.get("/addendums/{addendum_id}", response_model=ContractAddendumOut)
def get_addendum(addendum_id: int, db: Session = Depends(get_db)):
    """
    Busca aditivo por ID.
    """
    a = db.query(ContractAddendum).filter(ContractAddendum.id == addendum_id).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addendum not found")

    return ContractAddendumOut(**a.__dict__)


@router.put("/addendums/{addendum_id}", response_model=ContractAddendumOut, dependencies=[Depends(require_permissions("contracts.addendums.update"))])
def update_addendum_endpoint(
    addendum_id: int,
    data: ContractAddendumUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza aditivo contratual.
    """
    a = db.query(ContractAddendum).filter(ContractAddendum.id == addendum_id).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addendum not found")

    a = update_addendum(db, a, data)
    return ContractAddendumOut(**a.__dict__)
