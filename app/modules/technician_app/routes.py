"""
Arquivo: app/modules/technician_app/routes.py

Responsabilidade:
Rotas REST do App do Técnico: ordens atribuídas, início/conclusão, logs e
materiais consumidos.

Integrações:
- core.dependencies
- modules.technician_app.service
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, get_current_user, require_permissions
from ..users.models import User
from ..service_orders.models import ServiceOrder
from .schemas import (
    TechnicianProfileOut,
    AssignedOrderOut,
    WorkLogCreate,
    WorkLogOut,
    MaterialUsageCreate,
    MaterialUsageOut,
)
from .service import (
    get_profile_by_user,
    list_assigned_orders,
    start_order,
    complete_order,
    add_work_log,
    register_material_usage,
)


router = APIRouter()


@router.get("/profile", response_model=TechnicianProfileOut, dependencies=[Depends(require_permissions("technician.profile.read"))])
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prof = get_profile_by_user(db, user.id)
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de técnico não encontrado")
    return TechnicianProfileOut(**prof.__dict__)


@router.get("/orders/assigned", response_model=List[AssignedOrderOut], dependencies=[Depends(require_permissions("technician.orders.read"))])
def get_assigned_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = list_assigned_orders(db, user.username)
    return [AssignedOrderOut(**i.__dict__) for i in items]


@router.post("/orders/{order_id}/start", response_model=AssignedOrderOut, dependencies=[Depends(require_permissions("technician.orders.start"))])
def start_assigned_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OS não encontrada")
    order = start_order(db, order, user.username)
    return AssignedOrderOut(**order.__dict__)


@router.post("/orders/{order_id}/complete", response_model=AssignedOrderOut, dependencies=[Depends(require_permissions("technician.orders.complete"))])
def complete_assigned_order(order_id: int, notes: str = "", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OS não encontrada")
    order = complete_order(db, order, notes)
    return AssignedOrderOut(**order.__dict__)


@router.post("/orders/{order_id}/work-log", response_model=WorkLogOut, dependencies=[Depends(require_permissions("technician.worklogs.create"))])
def create_work_log(order_id: int, data: WorkLogCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wl = add_work_log(db, order_id=order_id, user_id=user.id, content=data.content)
    return WorkLogOut(**wl.__dict__)


@router.post("/orders/{order_id}/materials", response_model=MaterialUsageOut, dependencies=[Depends(require_permissions("technician.materials.register"))])
def register_material(order_id: int, data: MaterialUsageCreate, db: Session = Depends(get_db)):
    mu = register_material_usage(db, order_id=order_id, item_id=data.item_id, warehouse_id=data.warehouse_id, quantity=data.quantity, unit_cost=data.unit_cost)
    return MaterialUsageOut(**mu.__dict__)

