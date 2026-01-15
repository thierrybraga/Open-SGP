"""
Arquivo: app/modules/service_orders/service.py

Responsabilidade:
Regras de negócio para Ordens de Serviço: criar, atualizar, atribuir técnico,
agendar e concluir, gerenciando itens de checklist.

Integrações:
- modules.service_orders.models
"""

from datetime import datetime
from sqlalchemy.orm import Session
from .models import ServiceOrder, ServiceOrderItem
from .schemas import ServiceOrderCreate, ServiceOrderUpdate, ServiceOrderItemCreate, AssignTechnician


def create_order(db: Session, data: ServiceOrderCreate) -> ServiceOrder:
    order = ServiceOrder(
        client_id=data.client_id,
        contract_id=data.contract_id,
        ticket_id=data.ticket_id,
        type=data.type,
        priority=data.priority,
        status=data.status,
        technician_name=data.technician_name,
        scheduled_at=data.scheduled_at,
        notes=data.notes,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    for item in data.items:
        db.add(ServiceOrderItem(order_id=order.id, description=item.description, quantity=item.quantity))
    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order: ServiceOrder, data: ServiceOrderUpdate) -> ServiceOrder:
    for field, value in data.dict(exclude_none=True).items():
        setattr(order, field, value)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def add_item(db: Session, order: ServiceOrder, item: ServiceOrderItemCreate) -> ServiceOrderItem:
    it = ServiceOrderItem(order_id=order.id, description=item.description, quantity=item.quantity)
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


def assign_technician(db: Session, order: ServiceOrder, payload: AssignTechnician) -> ServiceOrder:
    order.technician_name = payload.technician_name
    order.status = "scheduled"
    order.scheduled_at = payload.scheduled_at or datetime.utcnow()
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def complete_order(db: Session, order: ServiceOrder) -> ServiceOrder:
    order.status = "completed"
    order.executed_at = datetime.utcnow()
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

