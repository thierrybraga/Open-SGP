"""
Arquivo: app/modules/plans/schemas.py

Responsabilidade:
Esquemas Pydantic para Planos.

Integrações:
- modules.plans.models
"""

from typing import Optional
from pydantic import BaseModel


class PlanBase(BaseModel):
    name: str
    category: str
    description: str
    download_speed_mbps: float = 0.0
    upload_speed_mbps: float = 0.0
    burst_enabled: bool = False
    burst_rate_percent: float = 0.0
    burst_threshold_seconds: int = 0
    price: float = 0.0
    loyalty_months: int = 0
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    description: Optional[str] = None
    download_speed_mbps: Optional[float] = None
    upload_speed_mbps: Optional[float] = None
    burst_enabled: Optional[bool] = None
    burst_rate_percent: Optional[float] = None
    burst_threshold_seconds: Optional[int] = None
    price: Optional[float] = None
    loyalty_months: Optional[int] = None
    is_active: Optional[bool] = None


class PlanOut(PlanBase):
    id: int

    class Config:
        from_attributes = True

