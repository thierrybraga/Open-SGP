"""
Arquivo: app/modules/billing/gateway/schemas.py

Responsabilidade:
Esquemas Pydantic para configuração de gateway e cobranças.

Integrações:
- modules.billing.gateway.models
"""

from typing import Optional
from pydantic import BaseModel


class GatewayConfigCreate(BaseModel):
    provider: str
    api_key: str
    enabled: bool = True


class GatewayConfigOut(BaseModel):
    id: int
    provider: str
    enabled: bool

    class Config:
        from_attributes = True


class ChargeCreate(BaseModel):
    title_id: int
    provider: Optional[str] = None


class ChargeOut(BaseModel):
    id: int
    title_id: int
    gateway_id: Optional[int]
    status: str
    reference: str
    amount: float
    payment_url: Optional[str]

    class Config:
        from_attributes = True


class ChargeStatusUpdate(BaseModel):
    status: str
    payment_url: Optional[str] = None
