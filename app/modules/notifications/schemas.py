"""
Arquivo: app/modules/notifications/schemas.py

Responsabilidade:
Schemas Pydantic para Notificações.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    type: str = "info"
    link: Optional[str] = None


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    type: str
    read: bool
    link: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
