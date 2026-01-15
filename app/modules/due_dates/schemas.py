"""
Arquivo: app/modules/due_dates/schemas.py

Responsabilidade:
Esquemas Pydantic para Configuração de Vencimentos.
"""

from typing import Optional
from pydantic import BaseModel, validator


class DueDateConfigCreate(BaseModel):
    client_id: Optional[int] = None
    plan_id: Optional[int] = None
    due_day: int
    notes: Optional[str] = None
    is_active: bool = True

    @validator('due_day')
    def validate_due_day(cls, v):
        if not 1 <= v <= 31:
            raise ValueError('due_day must be between 1 and 31')
        return v


class DueDateConfigUpdate(BaseModel):
    due_day: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('due_day')
    def validate_due_day(cls, v):
        if v is not None and not 1 <= v <= 31:
            raise ValueError('due_day must be between 1 and 31')
        return v


class DueDateConfigOut(BaseModel):
    id: int
    client_id: Optional[int]
    plan_id: Optional[int]
    due_day: int
    notes: Optional[str]
    is_active: bool
    priority: str

    class Config:
        from_attributes = True
