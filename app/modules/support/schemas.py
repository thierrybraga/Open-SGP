"""
Arquivo: app/modules/support/schemas.py

Responsabilidade:
Schemas Pydantic para validação de dados de suporte.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class CategoryResponse(CategoryCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OccurrenceCreate(BaseModel):
    client_id: Optional[int] = None
    contract_id: Optional[int] = None
    category: str = "general"
    severity: str = "medium"
    description: str
    ticket_id: Optional[int] = None
    service_order_id: Optional[int] = None

class OccurrenceUpdate(BaseModel):
    category: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    closed_at: Optional[datetime] = None
    ticket_id: Optional[int] = None
    service_order_id: Optional[int] = None

class OccurrenceOut(OccurrenceCreate):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TicketCreate(BaseModel):
    client_id: int
    contract_id: Optional[int] = None
    category_id: int
    assignee_id: Optional[int] = None
    subject: str
    description: str
    priority: str = "normal"
    origin: str = "manual"

class TicketUpdate(BaseModel):
    category_id: Optional[int] = None
    assignee_id: Optional[int] = None
    subject: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class MessageCreate(BaseModel):
    ticket_id: int
    user_id: Optional[int] = None
    content: str
    is_internal: bool = False
    attachment_url: Optional[str] = None

class MessageOut(MessageCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TicketOut(BaseModel):
    id: int
    protocol: Optional[str] = None
    client_id: int
    contract_id: Optional[int] = None
    category_id: int
    assignee_id: Optional[int] = None
    subject: str
    description: str
    priority: str
    status: str
    origin: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    sla_due_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True
