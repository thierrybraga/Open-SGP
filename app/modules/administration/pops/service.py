"""
Arquivo: app/modules/administration/pops/service.py

Responsabilidade:
Regras de negócio para POPs.

Integrações:
- modules.administration.pops.models
"""

from sqlalchemy.orm import Session
from .models import POP
from .schemas import POPCreate


def create_pop(db: Session, data: POPCreate) -> POP:
    pop = POP(**data.dict())
    db.add(pop)
    db.commit()
    db.refresh(pop)
    return pop

