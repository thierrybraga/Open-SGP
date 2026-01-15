"""
Arquivo: app/modules/administration/nas/service.py

Responsabilidade:
Regras de negócio para NAS.

Integrações:
- modules.administration.nas.models
"""

from sqlalchemy.orm import Session
from .models import NAS
from .schemas import NASCreate


def create_nas(db: Session, data: NASCreate) -> NAS:
    nas = NAS(**data.dict())
    db.add(nas)
    db.commit()
    db.refresh(nas)
    return nas

