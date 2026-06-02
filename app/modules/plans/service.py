"""
Arquivo: app/modules/plans/service.py

Responsabilidade:
Regras de negócio para criação e atualização de planos.

Integrações:
- modules.plans.models
"""

from sqlalchemy.orm import Session
from .models import Plan
from .schemas import PlanCreate, PlanUpdate
from ..network.service import sync_service_profile_for_plan


def create_plan(db: Session, data: PlanCreate) -> Plan:
    plan = Plan(**data.dict())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    if plan.category == "internet":
        sync_service_profile_for_plan(db, plan)
    return plan


def update_plan(db: Session, plan: Plan, data: PlanUpdate) -> Plan:
    for field, value in data.dict(exclude_none=True).items():
        setattr(plan, field, value)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    if plan.category == "internet":
        sync_service_profile_for_plan(db, plan)
    return plan

