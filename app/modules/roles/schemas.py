"""
Arquivo: app/modules/roles/schemas.py

Responsabilidade:
Esquemas Pydantic para roles.

Integrações:
- modules.roles.models
"""

from typing import List
from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    permissions: List[str] = []


class RoleOut(RoleBase):
    id: int
    permissions: List[str] = []

    class Config:
        from_attributes = True

