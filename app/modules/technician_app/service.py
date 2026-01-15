"""
Arquivo: app/modules/technician_app/service.py

Responsabilidade:
Regras de negócio do App do Técnico: ordens atribuídas, início/conclusão de OS,
registro de logs e consumo de materiais integrado ao estoque.

Integrações:
- modules.technician_app.models
- modules.service_orders.models
- modules.stock.service
"""

from datetime import datetime
from sqlalchemy.orm import Session

from .models import TechnicianProfile, TechnicianWorkLog, TechnicianMaterialUsage
from ..service_orders.models import ServiceOrder
from ..stock.service import register_movement
from ..stock.schemas import MovementCreate


def get_profile_by_user(db: Session, user_id: int) -> TechnicianProfile | None:
    return db.query(TechnicianProfile).filter(TechnicianProfile.user_id == user_id).first()


def list_assigned_orders(db: Session, username: str) -> list[ServiceOrder]:
    return db.query(ServiceOrder).filter(ServiceOrder.technician_name == username, ServiceOrder.status.in_(["scheduled", "in_progress"])) .all()


def start_order(db: Session, order: ServiceOrder, username: str) -> ServiceOrder:
    order.status = "in_progress"
    order.technician_name = username
    order.executed_at = datetime.utcnow()
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def complete_order(db: Session, order: ServiceOrder, notes: str | None = None) -> ServiceOrder:
    order.status = "completed"
    if notes:
        order.notes = (order.notes or "") + ("\n" + notes)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def add_work_log(db: Session, order_id: int, user_id: int, content: str) -> TechnicianWorkLog:
    wl = TechnicianWorkLog(order_id=order_id, user_id=user_id, content=content)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return wl


def register_material_usage(db: Session, order_id: int, item_id: int, warehouse_id: int, quantity: float, unit_cost: float | None = None) -> TechnicianMaterialUsage:
    mu = TechnicianMaterialUsage(order_id=order_id, item_id=item_id, warehouse_id=warehouse_id, quantity=quantity, unit_cost=unit_cost)
    db.add(mu)
    db.commit()
    db.refresh(mu)

    register_movement(db, MovementCreate(item_id=item_id, warehouse_id=warehouse_id, type="out", quantity=quantity, unit_cost=unit_cost))
    return mu

