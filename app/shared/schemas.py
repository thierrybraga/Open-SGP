"""
Arquivo: app/shared/schemas.py

Responsabilidade:
Define esquemas Pydantic base para respostas padrão e paginação.

Integrações:
- modules.* schemas
"""

from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class Message(BaseModel):
    message: str


class Paginated(BaseModel, Generic[T]):
    total: int
    items: List[T]

