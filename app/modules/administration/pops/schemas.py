"""
Arquivo: app/modules/administration/pops/schemas.py

Responsabilidade:
Esquemas Pydantic para POPs.

Integrações:
- modules.administration.pops.models
"""

from pydantic import BaseModel


class POPBase(BaseModel):
    name: str
    city: str
    address: str
    latitude: float
    longitude: float


class POPCreate(POPBase):
    pass


class POPOut(POPBase):
    id: int

    class Config:
        from_attributes = True

