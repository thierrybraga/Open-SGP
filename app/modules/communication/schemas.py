"""
Arquivo: app/modules/communication/schemas.py

Responsabilidade:
Esquemas Pydantic para templates e mensagens em fila.

Integrações:
- modules.communication.models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TemplateCreate(BaseModel):
    name: str
    channel: str
    content: str


class TemplateUpdate(BaseModel):
    content: Optional[str] = None


class TemplateOut(BaseModel):
    id: int
    name: str
    channel: str
    content: str

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    channel: str
    destination: str
    content: str
    template_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    contract_id: Optional[int] = None
    client_id: Optional[int] = None
    provider: Optional[str] = None


class MessageOut(BaseModel):
    id: int
    channel: str
    destination: str
    content: str
    template_id: Optional[int]
    contract_id: Optional[int]
    client_id: Optional[int]
    provider: Optional[str]
    provider_message_id: Optional[str]
    status: str
    scheduled_at: Optional[datetime]
    dispatched_at: Optional[datetime]
    error: Optional[str]

    class Config:
        from_attributes = True
