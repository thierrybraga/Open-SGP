"""
Arquivo: app/modules/users/schemas.py

Responsabilidade:
Esquemas Pydantic para criação, leitura e atualização de usuários.

Integrações:
- modules.users.models
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    id: int
    roles: List[str] = []

    class Config:
        from_attributes = True

