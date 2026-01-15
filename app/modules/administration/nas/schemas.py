"""
Arquivo: app/modules/administration/nas/schemas.py

Responsabilidade:
Esquemas Pydantic para NAS.

Integrações:
- modules.administration.nas.models
"""

from pydantic import BaseModel


class NASBase(BaseModel):
    name: str
    ip_address: str
    secret: str
    vendor: str
    pop_id: int | None = None


class NASCreate(NASBase):
    pass


class NASOut(NASBase):
    id: int

    class Config:
        from_attributes = True

