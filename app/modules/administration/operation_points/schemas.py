"""
Arquivo: app/modules/administration/operation_points/schemas.py

Responsabilidade:
Schemas Pydantic para Pontos de Operação.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class OperationPointCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    point_type: str  # office, store, service_center, warehouse
    address: str
    city: str
    state: str
    postal_code: Optional[str] = None
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    working_days: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator('point_type')
    @classmethod
    def validate_point_type(cls, v):
        valid_types = ['office', 'store', 'service_center', 'warehouse', 'attendance_point']
        if v not in valid_types:
            raise ValueError(f'point_type must be one of: {", ".join(valid_types)}')
        return v

    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        if len(v) != 2:
            raise ValueError('state must be a 2-letter code (e.g., SP, RJ)')
        return v.upper()


class OperationPointUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    point_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    working_days: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class OperationPointOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    point_type: str
    address: str
    city: str
    state: str
    postal_code: Optional[str] = None
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    working_days: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True
