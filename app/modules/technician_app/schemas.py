"""
Arquivo: app/modules/technician_app/schemas.py

Responsabilidade:
Esquemas Pydantic do App do Técnico: perfil, ordens atribuídas, logs e materiais.

Integrações:
- modules.technician_app.models
"""

from typing import Optional, List
from pydantic import BaseModel


class TechnicianProfileOut(BaseModel):
    user_id: int
    name: str
    phone: str
    skills: str

    class Config:
        from_attributes = True


class AssignedOrderOut(BaseModel):
    id: int
    type: str
    priority: str
    status: str
    scheduled_at: Optional[str]
    client_id: Optional[int]
    contract_id: Optional[int]

    class Config:
        from_attributes = True


class WorkLogCreate(BaseModel):
    content: str


class WorkLogOut(BaseModel):
    id: int
    order_id: int
    user_id: int
    content: str

    class Config:
        from_attributes = True


class MaterialUsageCreate(BaseModel):
    item_id: int
    warehouse_id: int
    quantity: float
    unit_cost: Optional[float] = None


class MaterialUsageOut(BaseModel):
    id: int
    order_id: int
    item_id: int
    warehouse_id: int
    quantity: float
    unit_cost: Optional[float]

    class Config:
        from_attributes = True

