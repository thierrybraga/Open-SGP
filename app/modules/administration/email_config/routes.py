"""
Arquivo: app/modules/administration/email_config/routes.py

Responsabilidade:
Rotas REST para Configuração de E-mail.

Integrações:
- core.dependencies
- modules.administration.email_config.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import EmailConfiguration
from .schemas import (
    EmailConfigurationCreate,
    EmailConfigurationUpdate,
    EmailConfigurationOut,
    EmailTestRequest,
    EmailTestResult
)
from .service import (
    create_email_configuration,
    update_email_configuration,
    get_default_email_configuration,
    test_email_configuration
)


router = APIRouter()


@router.get("/", response_model=List[EmailConfigurationOut])
def list_email_configurations(
    is_active: Optional[bool] = Query(default=None),
    company_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista configurações de email.
    """
    q = db.query(EmailConfiguration)

    if is_active is not None:
        q = q.filter(EmailConfiguration.is_active == is_active)
    if company_id is not None:
        q = q.filter(EmailConfiguration.company_id == company_id)

    configs = q.order_by(EmailConfiguration.is_default.desc(), EmailConfiguration.name).all()
    return [EmailConfigurationOut(**c.__dict__) for c in configs]


@router.post("/", response_model=EmailConfigurationOut, dependencies=[Depends(require_permissions("administration.email.create"))])
def create_email_configuration_endpoint(data: EmailConfigurationCreate, db: Session = Depends(get_db)):
    """
    Cria nova configuração de email.
    """
    try:
        config = create_email_configuration(db, data)
        return EmailConfigurationOut(**config.__dict__)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{config_id}", response_model=EmailConfigurationOut)
def get_email_configuration(config_id: int, db: Session = Depends(get_db)):
    """
    Busca configuração de email por ID.
    """
    config = db.query(EmailConfiguration).filter(EmailConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email configuration not found")

    return EmailConfigurationOut(**config.__dict__)


@router.put("/{config_id}", response_model=EmailConfigurationOut, dependencies=[Depends(require_permissions("administration.email.update"))])
def update_email_configuration_endpoint(
    config_id: int,
    data: EmailConfigurationUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza configuração de email.
    """
    config = db.query(EmailConfiguration).filter(EmailConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email configuration not found")

    config = update_email_configuration(db, config, data)
    return EmailConfigurationOut(**config.__dict__)


@router.delete("/{config_id}", dependencies=[Depends(require_permissions("administration.email.delete"))])
def delete_email_configuration(config_id: int, db: Session = Depends(get_db)):
    """
    Remove configuração de email.
    """
    config = db.query(EmailConfiguration).filter(EmailConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email configuration not found")

    if config.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default email configuration. Set another as default first."
        )

    db.delete(config)
    db.commit()

    return {"message": "Email configuration deleted successfully"}


@router.get("/default/get", response_model=EmailConfigurationOut)
def get_default_configuration(db: Session = Depends(get_db)):
    """
    Retorna configuração padrão de email.
    """
    config = get_default_email_configuration(db)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No default email configuration found")

    return EmailConfigurationOut(**config.__dict__)


@router.post("/{config_id}/test", response_model=EmailTestResult, dependencies=[Depends(require_permissions("administration.email.test"))])
def test_email_configuration_endpoint(
    config_id: int,
    test_request: EmailTestRequest,
    db: Session = Depends(get_db)
):
    """
    Testa configuração de email enviando um e-mail de teste.
    """
    config = db.query(EmailConfiguration).filter(EmailConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email configuration not found")

    result = test_email_configuration(db, config, test_request)
    return EmailTestResult(**result)


@router.post("/{config_id}/set-default", response_model=EmailConfigurationOut, dependencies=[Depends(require_permissions("administration.email.update"))])
def set_as_default(config_id: int, db: Session = Depends(get_db)):
    """
    Define esta configuração como padrão.
    """
    config = db.query(EmailConfiguration).filter(EmailConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email configuration not found")

    # Remover default das outras
    db.query(EmailConfiguration).update({"is_default": False})

    # Setar como default
    config.is_default = True
    db.add(config)
    db.commit()
    db.refresh(config)

    return EmailConfigurationOut(**config.__dict__)
