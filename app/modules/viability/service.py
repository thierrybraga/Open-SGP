"""
Arquivo: app/modules/viability/service.py

Responsabilidade:
Regras de negócio para Viabilidade Técnica.

Integrações:
- modules.viability.models
- modules.clients.models
- modules.plans.models
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .models import Viability
from .schemas import ViabilityCreate, ViabilityUpdate, ViabilityAnalyze
from ..clients.models import Client
from ..plans.models import Plan


def create_viability(db: Session, data: ViabilityCreate, user_id: int = None) -> Viability:
    """
    Cria uma nova análise de viabilidade técnica.
    """
    # Validar cliente
    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise ValueError("Client not found")

    # Validar plano
    plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
    if not plan:
        raise ValueError("Plan not found")

    # Criar viabilidade
    viability = Viability(**data.dict())
    viability.status = "pending"
    viability.expires_at = datetime.utcnow() + timedelta(days=30)  # Expira em 30 dias

    db.add(viability)
    db.commit()
    db.refresh(viability)

    return viability


def update_viability(db: Session, viability: Viability, data: ViabilityUpdate) -> Viability:
    """
    Atualiza dados de uma viabilidade.
    """
    for field, value in data.dict(exclude_none=True).items():
        setattr(viability, field, value)

    db.add(viability)
    db.commit()
    db.refresh(viability)

    return viability


def analyze_viability(db: Session, viability: Viability, data: ViabilityAnalyze, user_id: int) -> Viability:
    """
    Analisa e aprova/rejeita uma viabilidade técnica.
    """
    if viability.status not in ["pending"]:
        raise ValueError("Viability already analyzed")

    if data.status not in ["approved", "rejected"]:
        raise ValueError("Status must be approved or rejected")

    # Atualizar dados técnicos
    for field, value in data.dict(exclude_none=True).items():
        setattr(viability, field, value)

    # Marcar como analisado
    viability.analyzed_by = user_id
    viability.analyzed_at = datetime.utcnow()

    db.add(viability)
    db.commit()
    db.refresh(viability)

    return viability


def get_pending_viabilities(db: Session, skip: int = 0, limit: int = 100):
    """
    Lista viabilidades pendentes de análise.
    """
    return db.query(Viability).filter(
        Viability.status == "pending",
        Viability.expires_at > datetime.utcnow()
    ).offset(skip).limit(limit).all()


def check_expired_viabilities(db: Session):
    """
    Marca viabilidades expiradas.
    """
    expired = db.query(Viability).filter(
        Viability.status == "pending",
        Viability.expires_at <= datetime.utcnow()
    ).all()

    for v in expired:
        v.status = "expired"
        db.add(v)

    db.commit()
    return len(expired)
