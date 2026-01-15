"""
Arquivo: app/modules/tech_app/service.py

Responsabilidade:
Lógica do App do Técnico: listagem de OS, execução e finalização.

Integrações:
- modules.service_orders.models
- modules.users.models
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..service_orders.models import ServiceOrder, ServiceOrderHistory
from ..users.models import User
from datetime import datetime


def list_my_orders(db: Session, user_id: int) -> list[ServiceOrder]:
    """Lista OS atribuídas ao técnico, pendentes ou em progresso."""
    return db.query(ServiceOrder).filter(
        ServiceOrder.assigned_to == user_id,
        ServiceOrder.status.in_(["open", "assigned", "in_progress"])
    ).order_by(ServiceOrder.scheduled_at).all()


def get_order_details(db: Session, order_id: int) -> ServiceOrder | None:
    return db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()


def start_order(db: Session, order_id: int, user_id: int) -> ServiceOrder:
    order = db.query(ServiceOrder).get(order_id)
    if not order:
        raise ValueError("Order not found")
    
    order.status = "in_progress"
    order.updated_at = datetime.utcnow()
    
    # Add history
    hist = ServiceOrderHistory(
        service_order_id=order.id,
        status="in_progress",
        notes="Técnico iniciou o atendimento.",
        created_by=user_id
    )
    db.add(hist)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def finish_order(db: Session, order_id: int, user_id: int, notes: str) -> ServiceOrder:
    order = db.query(ServiceOrder).get(order_id)
    if not order:
        raise ValueError("Order not found")
    
    order.status = "completed"
    order.updated_at = datetime.utcnow()
    
    hist = ServiceOrderHistory(
        service_order_id=order.id,
        status="completed",
        notes=f"Finalizado pelo técnico. Obs: {notes}",
        created_by=user_id
    )
    db.add(hist)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
