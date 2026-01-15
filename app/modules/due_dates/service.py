"""
Arquivo: app/modules/due_dates/service.py

Responsabilidade:
Lógica de negócio para Vencimentos.
"""

from sqlalchemy.orm import Session
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from .models import DueDateConfig
from .schemas import DueDateConfigCreate, DueDateConfigUpdate


def create_due_date_config(db: Session, data: DueDateConfigCreate) -> DueDateConfig:
    """
    Cria configuração de vencimento.
    """
    # Determinar prioridade
    if data.client_id:
        priority = "client"
    elif data.plan_id:
        priority = "plan"
    else:
        priority = "global"

    config = DueDateConfig(**data.dict())
    config.priority = priority

    db.add(config)
    db.commit()
    db.refresh(config)

    return config


def update_due_date_config(db: Session, config: DueDateConfig, data: DueDateConfigUpdate) -> DueDateConfig:
    """
    Atualiza configuração de vencimento.
    """
    for field, value in data.dict(exclude_none=True).items():
        setattr(config, field, value)

    db.add(config)
    db.commit()
    db.refresh(config)

    return config


def get_due_date_for_contract(db: Session, client_id: int, plan_id: int, base_date: date = None) -> date:
    """
    Retorna data de vencimento baseado nas configurações.
    Ordem de prioridade: client > plan > global
    """
    if base_date is None:
        base_date = date.today()

    # Buscar configuração por cliente
    client_config = db.query(DueDateConfig).filter(
        DueDateConfig.client_id == client_id,
        DueDateConfig.is_active == True
    ).first()

    if client_config:
        return calculate_due_date(base_date, client_config.due_day)

    # Buscar configuração por plano
    plan_config = db.query(DueDateConfig).filter(
        DueDateConfig.plan_id == plan_id,
        DueDateConfig.is_active == True
    ).first()

    if plan_config:
        return calculate_due_date(base_date, plan_config.due_day)

    # Buscar configuração global
    global_config = db.query(DueDateConfig).filter(
        DueDateConfig.client_id.is_(None),
        DueDateConfig.plan_id.is_(None),
        DueDateConfig.is_active == True
    ).first()

    if global_config:
        return calculate_due_date(base_date, global_config.due_day)

    # Default: dia 10 do próximo mês
    return calculate_due_date(base_date, 10)


def calculate_due_date(base_date: date, due_day: int) -> date:
    """
    Calcula data de vencimento baseado no dia configurado.
    """
    # Próximo mês
    next_month = base_date + relativedelta(months=1)

    # Ajustar para o dia configurado
    try:
        due_date = next_month.replace(day=due_day)
    except ValueError:
        # Se o dia não existe no mês (ex: 31 em fevereiro), usar último dia do mês
        due_date = next_month + relativedelta(day=31)

    return due_date
