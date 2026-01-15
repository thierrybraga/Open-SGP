"""
Arquivo: app/modules/administration/variables/schemas.py

Responsabilidade:
Esquemas Pydantic para variáveis de sistema.

Integrações:
- modules.administration.variables.models
"""

from pydantic import BaseModel


class VariableCreate(BaseModel):
    key: str
    value: str
    description: str


class VariableOut(BaseModel):
    id: int
    key: str
    value: str
    description: str

    class Config:
        from_attributes = True

