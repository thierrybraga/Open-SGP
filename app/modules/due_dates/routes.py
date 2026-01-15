"""
Arquivo: app/modules/due_dates/routes.py

Responsabilidade:
Rotas REST para Configuração de Vencimentos.

Integrações:
- core.dependencies
- modules.due_dates.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date

from ...core.dependencies import get_db, require_permissions
from .models import DueDateConfig
from .schemas import DueDateConfigCreate, DueDateConfigUpdate, DueDateConfigOut
from .service import create_due_date_config, update_due_date_config, get_due_date_for_contract


router = APIRouter()


@router.get("/", response_model=List[DueDateConfigOut])
def list_due_date_configs(
    client_id: Optional[int] = Query(default=None),
    plan_id: Optional[int] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista configurações de vencimento.
    """
    q = db.query(DueDateConfig)

    if client_id is not None:
        q = q.filter(DueDateConfig.client_id == client_id)
    if plan_id is not None:
        q = q.filter(DueDateConfig.plan_id == plan_id)
    if is_active is not None:
        q = q.filter(DueDateConfig.is_active == is_active)

    configs = q.order_by(DueDateConfig.priority.desc(), DueDateConfig.created_at.desc()).all()
    return [DueDateConfigOut(**c.__dict__) for c in configs]


@router.post("/", response_model=DueDateConfigOut, dependencies=[Depends(require_permissions("due_dates.create"))])
def create_due_date_config_endpoint(
    data: DueDateConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Cria configuração de vencimento.
    """
    # Validar que não existe configuração duplicada ativa
    q = db.query(DueDateConfig).filter(DueDateConfig.is_active == True)

    if data.client_id:
        q = q.filter(DueDateConfig.client_id == data.client_id)
    elif data.plan_id:
        q = q.filter(DueDateConfig.plan_id == data.plan_id)
    else:
        q = q.filter(
            DueDateConfig.client_id.is_(None),
            DueDateConfig.plan_id.is_(None)
        )

    existing = q.first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active configuration already exists for this scope"
        )

    config = create_due_date_config(db, data)
    return DueDateConfigOut(**config.__dict__)


@router.get("/{config_id}", response_model=DueDateConfigOut)
def get_due_date_config(config_id: int, db: Session = Depends(get_db)):
    """
    Busca configuração de vencimento por ID.
    """
    config = db.query(DueDateConfig).filter(DueDateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")

    return DueDateConfigOut(**config.__dict__)


@router.put("/{config_id}", response_model=DueDateConfigOut, dependencies=[Depends(require_permissions("due_dates.update"))])
def update_due_date_config_endpoint(
    config_id: int,
    data: DueDateConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza configuração de vencimento.
    """
    config = db.query(DueDateConfig).filter(DueDateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")

    config = update_due_date_config(db, config, data)
    return DueDateConfigOut(**config.__dict__)


@router.delete("/{config_id}", dependencies=[Depends(require_permissions("due_dates.delete"))])
def delete_due_date_config(config_id: int, db: Session = Depends(get_db)):
    """
    Remove configuração de vencimento.
    """
    config = db.query(DueDateConfig).filter(DueDateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")

    db.delete(config)
    db.commit()

    return {"message": "Configuration deleted successfully"}


@router.get("/calculate/contract")
def calculate_due_date_for_contract(
    client_id: int = Query(...),
    plan_id: int = Query(...),
    base_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Calcula data de vencimento para um contrato baseado nas configurações.
    """
    due_date = get_due_date_for_contract(db, client_id, plan_id, base_date)

    return {
        "client_id": client_id,
        "plan_id": plan_id,
        "base_date": base_date or date.today(),
        "due_date": due_date
    }
