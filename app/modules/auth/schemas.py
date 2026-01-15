"""
Arquivo: app/modules/auth/schemas.py

Responsabilidade:
Esquemas Pydantic para autenticação e emissão de token.

Integrações:
- modules.auth.routes
"""

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Login(BaseModel):
    username: str
    password: str

