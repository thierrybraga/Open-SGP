"""
Arquivo: app/modules/customer_app/schemas.py

Responsabilidade:
Esquemas Pydantic para App do Cliente: perfil, preferências, tokens e listagens.

Integrações:
- modules.customer_app.models
"""

from typing import Optional, Any, List, Dict
from pydantic import BaseModel


class PreferenceUpdate(BaseModel):
    notify_email: Optional[bool] = None
    notify_sms: Optional[bool] = None
    notify_whatsapp: Optional[bool] = None


class PreferenceOut(BaseModel):
    client_id: int
    notify_email: bool
    notify_sms: bool
    notify_whatsapp: bool

    class Config:
        from_attributes = True


class DeviceTokenCreate(BaseModel):
    platform: str
    token: str


class DeviceTokenOut(BaseModel):
    id: int
    platform: str
    token: str

    class Config:
        from_attributes = True


class ProfileOut(BaseModel):
    client_id: int
    name: str
    email: str
    phone: str
    contracts_active: int
    titles_overdue: int
    amount_overdue: float


class ContractOut(BaseModel):
    id: int
    status: str
    billing_day: int
    installation_address: str

    class Config:
        from_attributes = True


class TitleOut(BaseModel):
    id: int
    contract_id: int
    due_date: Any
    amount: float
    status: str
    payment_slip_url: Optional[str]

    class Config:
        from_attributes = True


class TicketCreate(BaseModel):
    contract_id: Optional[int] = None
    subject: str
    category: str
    priority: str


class TicketOut(BaseModel):
    id: int
    status: str
    subject: str
    category: str
    priority: str

    class Config:
        from_attributes = True


class CustomerLogin(BaseModel):
    username: str  # email or cpf
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

