"""
Arquivo: app/modules/permissions/schemas.py

Responsabilidade:
Esquemas Pydantic para permissões.

Integrações:
- modules.permissions.models
"""

from pydantic import BaseModel


class PermissionCreate(BaseModel):
    code: str
    description: str


class PermissionOut(BaseModel):
    id: int
    code: str
    description: str

    class Config:
        from_attributes = True

