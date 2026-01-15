"""
Arquivo: app/modules/service_orders/schemas.py

Responsabilidade:
Esquemas Pydantic para Ordens de Serviço e itens.

Integrações:
- modules.service_orders.models
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ServiceOrderItemCreate(BaseModel):
    description: str
    quantity: int = 1


class ServiceOrderItemOut(ServiceOrderItemCreate):
    id: int
    done: bool

    class Config:
        from_attributes = True


class ServiceOrderBase(BaseModel):
    client_id: Optional[int] = None
    contract_id: Optional[int] = None
    ticket_id: Optional[int] = None
    type: str
    priority: str
    status: str = "open"
    technician_name: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[ServiceOrderItemCreate] = []


class ServiceOrderCreate(ServiceOrderBase):
    pass


class ServiceOrderUpdate(BaseModel):
    status: Optional[str] = None
    technician_name: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    notes: Optional[str] = None


class AssignTechnician(BaseModel):
    technician_name: str
    scheduled_at: Optional[datetime] = None


class ServiceOrderOut(ServiceOrderBase):
    id: int
    executed_at: Optional[datetime]
    items: List[ServiceOrderItemOut]

    class Config:
        from_attributes = True

