"""
Arquivo: app/modules/contract_templates/service.py

Responsabilidade:
Regras de negócio para Templates de Contrato e Aditivos.

Integrações:
- modules.contract_templates.models
- modules.contracts.models
"""

from datetime import datetime
from sqlalchemy.orm import Session
import re

from .models import ContractTemplate, ContractAddendum
from .schemas import (
    ContractTemplateCreate,
    ContractTemplateUpdate,
    ContractAddendumCreate,
    ContractAddendumUpdate,
    GenerateContractRequest
)
from ..contracts.models import Contract
from ..clients.models import Client
from ..plans.models import Plan


def create_template(db: Session, data: ContractTemplateCreate, user_id: int) -> ContractTemplate:
    """
    Cria um novo template de contrato.
    """
    # Se marcar como default, desmarcar os outros
    if data.is_default:
        db.query(ContractTemplate).update({"is_default": False})

    template = ContractTemplate(**data.dict())
    template.created_by = user_id

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


def update_template(db: Session, template: ContractTemplate, data: ContractTemplateUpdate) -> ContractTemplate:
    """
    Atualiza um template de contrato.
    """
    # Se marcar como default, desmarcar os outros
    if data.is_default and data.is_default != template.is_default:
        db.query(ContractTemplate).filter(ContractTemplate.id != template.id).update({"is_default": False})

    for field, value in data.dict(exclude_none=True).items():
        setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


def generate_contract_from_template(db: Session, data: GenerateContractRequest) -> str:
    """
    Gera um contrato a partir de um template, substituindo variáveis.
    """
    template = db.query(ContractTemplate).filter(ContractTemplate.id == data.template_id).first()
    if not template:
        raise ValueError("Template not found")

    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise ValueError("Contract not found")

    # Buscar dados relacionados
    client = db.query(Client).filter(Client.id == contract.client_id).first()
    plan = db.query(Plan).filter(Plan.id == contract.plan_id).first()

    # Variáveis padrão
    variables = {
        "client_name": client.name if client else "",
        "client_document": client.document if client else "",
        "client_email": client.email if client else "",
        "client_phone": client.phone if client else "",
        "plan_name": plan.name if plan else "",
        "plan_speed": plan.download_speed if plan else "",
        "plan_price": f"{plan.price:.2f}" if plan else "",
        "contract_number": str(contract.id),
        "contract_start_date": contract.start_date.strftime("%d/%m/%Y") if contract.start_date else "",
        "current_date": datetime.now().strftime("%d/%m/%Y"),
    }

    # Adicionar variáveis customizadas
    if data.variables:
        variables.update(data.variables)

    # Substituir variáveis no template
    content = template.content
    for key, value in variables.items():
        content = re.sub(r'\{\{' + key + r'\}\}', str(value), content)

    return content


def create_addendum(db: Session, data: ContractAddendumCreate, user_id: int) -> ContractAddendum:
    """
    Cria um aditivo contratual.
    """
    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise ValueError("Contract not found")

    # Determinar número do aditivo
    last_addendum = db.query(ContractAddendum).filter(
        ContractAddendum.contract_id == data.contract_id
    ).order_by(ContractAddendum.addendum_number.desc()).first()

    addendum_number = 1 if not last_addendum else last_addendum.addendum_number + 1

    # Criar aditivo
    addendum = ContractAddendum(**data.dict())
    addendum.addendum_number = addendum_number
    addendum.created_by = user_id

    db.add(addendum)
    db.commit()
    db.refresh(addendum)

    return addendum


def update_addendum(db: Session, addendum: ContractAddendum, data: ContractAddendumUpdate) -> ContractAddendum:
    """
    Atualiza um aditivo contratual.
    """
    for field, value in data.dict(exclude_none=True).items():
        setattr(addendum, field, value)

    db.add(addendum)
    db.commit()
    db.refresh(addendum)

    return addendum
