"""
Arquivo: app/modules/tech_app/schemas.py

Responsabilidade:
Schemas Pydantic para o App do Técnico.
"""

from pydantic import BaseModel
from typing import Optional

class TechOrderAction(BaseModel):
    notes: Optional[str] = None
