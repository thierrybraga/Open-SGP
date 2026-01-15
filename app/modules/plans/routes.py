"""
Arquivo: app/modules/plans/routes.py

Responsabilidade:
Rotas REST para planos, com filtros por categoria, ativo e faixa de preço.

Integrações:
- core.dependencies
- modules.plans.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Plan
from .schemas import PlanCreate, PlanUpdate, PlanOut
from .service import create_plan, update_plan


router = APIRouter()


@router.get("/", response_model=List[PlanOut])
def list_plans(
    category: Optional[str] = Query(default=None),
    active: Optional[bool] = Query(default=None),
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Plan)
    if category:
        q = q.filter(Plan.category == category)
    if active is not None:
        q = q.filter(Plan.is_active == active)
    if min_price is not None:
        q = q.filter(Plan.price >= min_price)
    if max_price is not None:
        q = q.filter(Plan.price <= max_price)
    items = q.all()
    return [PlanOut(**p.__dict__) for p in items]


@router.post("/", response_model=PlanOut, dependencies=[Depends(require_permissions("plans.create"))])
def create_plan_endpoint(data: PlanCreate, db: Session = Depends(get_db)):
    if db.query(Plan).filter(Plan.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan name already exists")
    p = create_plan(db, data)
    return PlanOut(**p.__dict__)


@router.put("/{plan_id}", response_model=PlanOut, dependencies=[Depends(require_permissions("plans.update"))])
def update_plan_endpoint(plan_id: int, data: PlanUpdate, db: Session = Depends(get_db)):
    p = db.query(Plan).filter(Plan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    p = update_plan(db, p, data)
    return PlanOut(**p.__dict__)


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    p = db.query(Plan).filter(Plan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return PlanOut(**p.__dict__)

