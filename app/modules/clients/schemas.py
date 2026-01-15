"""
Arquivo: app/modules/clients/schemas.py

Responsabilidade:
Esquemas Pydantic para Clientes com endereços e contatos.

Integrações:
- modules.clients.models
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr


class AddressIn(BaseModel):
    street: str
    number: str
    neighborhood: str
    city: str
    state: str
    zipcode: str
    is_primary: bool = False


class ContactIn(BaseModel):
    name: str
    phone: str
    email: EmailStr
    role: str


class ClientBase(BaseModel):
    person_type: str  # PF/PJ
    name: str
    document: str
    email: EmailStr
    phone: str


class ClientCreate(ClientBase):
    addresses: List[AddressIn] = []
    contacts: List[ContactIn] = []


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class AddressOut(AddressIn):
    id: int

    class Config:
        from_attributes = True


class ContactOut(ContactIn):
    id: int

    class Config:
        from_attributes = True


class ClientOut(ClientBase):
    id: int
    is_active: bool
    addresses: List[AddressOut] = []
    contacts: List[ContactOut] = []

    class Config:
        from_attributes = True

