"""
Arquivo: app/modules/service_orders/routes.py

Responsabilidade:
Rotas REST para Ordens de Serviço: listar, criar, atualizar, atribuir técnico,
agendar, concluir e gerenciar itens.

Integrações:
- core.dependencies
- modules.service_orders.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import ServiceOrder, ServiceOrderItem
from .schemas import (
    ServiceOrderCreate,
    ServiceOrderUpdate,
    ServiceOrderOut,
    ServiceOrderItemCreate,
    ServiceOrderItemOut,
    AssignTechnician,
)
from .service import create_order, update_order, add_item, assign_technician, complete_order


router = APIRouter()


@router.get("/orders", response_model=List[ServiceOrderOut])
def list_orders(
    status_: Optional[str] = Query(default=None, alias="status"),
    type_: Optional[str] = Query(default=None, alias="type"),
    technician: Optional[str] = Query(default=None),
    contract_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(ServiceOrder)
    if status_:
        q = q.filter(ServiceOrder.status == status_)
    if type_:
        q = q.filter(ServiceOrder.type == type_)
    if technician:
        q = q.filter(ServiceOrder.technician_name == technician)
    if contract_id:
        q = q.filter(ServiceOrder.contract_id == contract_id)
    items = q.all()
    out: List[ServiceOrderOut] = []
    for o in items:
        out.append(
            ServiceOrderOut(
                id=o.id,
                client_id=o.client_id,
                contract_id=o.contract_id,
                ticket_id=o.ticket_id,
                type=o.type,
                priority=o.priority,
                status=o.status,
                technician_name=o.technician_name,
                scheduled_at=o.scheduled_at,
                executed_at=o.executed_at,
                notes=o.notes,
                items=[ServiceOrderItemOut(**i.__dict__) for i in o.items],
            )
        )
    return out


@router.post("/orders", response_model=ServiceOrderOut, dependencies=[Depends(require_permissions("service_orders.create"))])
def create_order_endpoint(data: ServiceOrderCreate, db: Session = Depends(get_db)):
    o = create_order(db, data)
    return ServiceOrderOut(
        id=o.id,
        client_id=o.client_id,
        contract_id=o.contract_id,
        ticket_id=o.ticket_id,
        type=o.type,
        priority=o.priority,
        status=o.status,
        technician_name=o.technician_name,
        scheduled_at=o.scheduled_at,
        executed_at=o.executed_at,
        notes=o.notes,
        items=[ServiceOrderItemOut(**i.__dict__) for i in o.items],
    )


@router.put("/orders/{order_id}", response_model=ServiceOrderOut, dependencies=[Depends(require_permissions("service_orders.update"))])
def update_order_endpoint(order_id: int, data: ServiceOrderUpdate, db: Session = Depends(get_db)):
    o = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order not found")
    o = update_order(db, o, data)
    return ServiceOrderOut(
        id=o.id,
        client_id=o.client_id,
        contract_id=o.contract_id,
        ticket_id=o.ticket_id,
        type=o.type,
        priority=o.priority,
        status=o.status,
        technician_name=o.technician_name,
        scheduled_at=o.scheduled_at,
        executed_at=o.executed_at,
        notes=o.notes,
        items=[ServiceOrderItemOut(**i.__dict__) for i in o.items],
    )


@router.post("/orders/{order_id}/items", response_model=ServiceOrderItemOut, dependencies=[Depends(require_permissions("service_orders.update"))])
def add_item_endpoint(order_id: int, item: ServiceOrderItemCreate, db: Session = Depends(get_db)):
    o = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order not found")
    it = add_item(db, o, item)
    return ServiceOrderItemOut(**it.__dict__)


@router.post("/orders/{order_id}/assign", response_model=ServiceOrderOut, dependencies=[Depends(require_permissions("service_orders.assign"))])
def assign_technician_endpoint(order_id: int, payload: AssignTechnician, db: Session = Depends(get_db)):
    o = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order not found")
    o = assign_technician(db, o, payload)
    return ServiceOrderOut(
        id=o.id,
        client_id=o.client_id,
        contract_id=o.contract_id,
        ticket_id=o.ticket_id,
        type=o.type,
        priority=o.priority,
        status=o.status,
        technician_name=o.technician_name,
        scheduled_at=o.scheduled_at,
        executed_at=o.executed_at,
        notes=o.notes,
        items=[ServiceOrderItemOut(**i.__dict__) for i in o.items],
    )


@router.post("/orders/{order_id}/complete", response_model=ServiceOrderOut, dependencies=[Depends(require_permissions("service_orders.close"))])
def complete_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    o = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order not found")
    o = complete_order(db, o)
    return ServiceOrderOut(
        id=o.id,
        client_id=o.client_id,
        contract_id=o.contract_id,
        ticket_id=o.ticket_id,
        type=o.type,
        priority=o.priority,
        status=o.status,
        technician_name=o.technician_name,
        scheduled_at=o.scheduled_at,
        executed_at=o.executed_at,
        notes=o.notes,
        items=[ServiceOrderItemOut(**i.__dict__) for i in o.items],
    )


@router.get("/orders/{order_id}", response_model=ServiceOrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service Order not found")
    return ServiceOrderOut(
        id=o.id,
        client_id=o.client_id,
        contract_id=o.contract_id,
        ticket_id=o.ticket_id,
        type=o.type,
        priority=o.priority,
        status=o.status,
        technician_name=o.technician_name,
        scheduled_at=o.scheduled_at,
        executed_at=o.executed_at,
        notes=o.notes,
        items=[ServiceOrderItemOut(**i.__dict__) for i in o.items],
    )

