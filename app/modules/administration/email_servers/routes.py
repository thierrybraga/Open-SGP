"""
Arquivo: app/modules/administration/email_servers/routes.py

Responsabilidade:
Rotas REST para Email Servers.

Integrações:
- core.dependencies
- modules.administration.email_servers.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import EmailServer
from .schemas import EmailServerCreate, EmailServerUpdate, EmailServerOut, EmailTestRequest
from .service import create_email_server, update_email_server, get_default_email_server, test_email_server


router = APIRouter()


@router.get("/", response_model=List[EmailServerOut])
def list_email_servers(
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista servidores de e-mail.
    """
    q = db.query(EmailServer)

    if is_active is not None:
        q = q.filter(EmailServer.is_active == is_active)

    servers = q.order_by(EmailServer.created_at.desc()).all()

    # Remover senha da resposta
    result = []
    for s in servers:
        server_dict = s.__dict__.copy()
        server_dict.pop('smtp_password', None)
        server_dict.pop('_sa_instance_state', None)
        result.append(EmailServerOut(**server_dict))

    return result


@router.post("/", response_model=EmailServerOut, dependencies=[Depends(require_permissions("administration.email_servers.create"))])
def create_email_server_endpoint(data: EmailServerCreate, db: Session = Depends(get_db)):
    """
    Cria servidor de e-mail.
    """
    server = create_email_server(db, data)
    server_dict = server.__dict__.copy()
    server_dict.pop('smtp_password', None)
    server_dict.pop('_sa_instance_state', None)
    return EmailServerOut(**server_dict)


@router.get("/{server_id}", response_model=EmailServerOut)
def get_email_server(server_id: int, db: Session = Depends(get_db)):
    """
    Busca servidor de e-mail por ID.
    """
    server = db.query(EmailServer).filter(EmailServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email server not found")

    server_dict = server.__dict__.copy()
    server_dict.pop('smtp_password', None)
    server_dict.pop('_sa_instance_state', None)
    return EmailServerOut(**server_dict)


@router.put("/{server_id}", response_model=EmailServerOut, dependencies=[Depends(require_permissions("administration.email_servers.update"))])
def update_email_server_endpoint(
    server_id: int,
    data: EmailServerUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza servidor de e-mail.
    """
    server = db.query(EmailServer).filter(EmailServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email server not found")

    server = update_email_server(db, server, data)
    server_dict = server.__dict__.copy()
    server_dict.pop('smtp_password', None)
    server_dict.pop('_sa_instance_state', None)
    return EmailServerOut(**server_dict)


@router.delete("/{server_id}", dependencies=[Depends(require_permissions("administration.email_servers.delete"))])
def delete_email_server(server_id: int, db: Session = Depends(get_db)):
    """
    Remove servidor de e-mail.
    """
    server = db.query(EmailServer).filter(EmailServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email server not found")

    db.delete(server)
    db.commit()

    return {"message": "Email server deleted successfully"}


@router.get("/default/get", response_model=EmailServerOut)
def get_default_email_server_endpoint(db: Session = Depends(get_db)):
    """
    Retorna servidor de e-mail padrão.
    """
    server = get_default_email_server(db)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No default email server found")

    server_dict = server.__dict__.copy()
    server_dict.pop('smtp_password', None)
    server_dict.pop('_sa_instance_state', None)
    return EmailServerOut(**server_dict)


@router.post("/{server_id}/test", dependencies=[Depends(require_permissions("administration.email_servers.test"))])
def test_email_server_endpoint(
    server_id: int,
    test_data: EmailTestRequest,
    db: Session = Depends(get_db)
):
    """
    Testa servidor de e-mail enviando um e-mail de teste.
    """
    result = test_email_server(db, server_id, test_data)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Test failed"))

    return result
