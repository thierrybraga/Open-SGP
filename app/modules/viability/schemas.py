"""
Arquivo: app/modules/viability/schemas.py

Responsabilidade:
Esquemas Pydantic para Viabilidade Técnica.

Integrações:
- modules.viability.models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ViabilityCreate(BaseModel):
    client_id: int
    address_id: Optional[int] = None
    plan_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    technician_notes: Optional[str] = None


class ViabilityUpdate(BaseModel):
    status: Optional[str] = None
    distance_to_pop: Optional[float] = None
    signal_quality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    equipment_needed: Optional[str] = None
    estimated_cost: Optional[float] = None
    installation_complexity: Optional[str] = None
    technician_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ViabilityAnalyze(BaseModel):
    status: str  # approved ou rejected
    distance_to_pop: Optional[float] = None
    signal_quality: Optional[str] = None
    equipment_needed: Optional[str] = None
    estimated_cost: Optional[float] = None
    installation_complexity: Optional[str] = None
    technician_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ViabilityOut(BaseModel):
    id: int
    client_id: int
    address_id: Optional[int]
    plan_id: int
    status: str
    distance_to_pop: Optional[float]
    signal_quality: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    equipment_needed: Optional[str]
    estimated_cost: Optional[float]
    installation_complexity: Optional[str]
    technician_notes: Optional[str]
    rejection_reason: Optional[str]
    analyzed_by: Optional[int]
    analyzed_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
