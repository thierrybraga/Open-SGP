"""
Arquivo: app/modules/communication/routes.py

Responsabilidade:
Rotas REST para comunicação: templates, fila de mensagens, envio e reprocesso.

Integrações:
- core.dependencies
- modules.communication.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Template, MessageQueue
from .schemas import TemplateCreate, TemplateUpdate, TemplateOut, MessageCreate, MessageOut
from .service import create_template, update_template, enqueue_message, dispatch_message, requeue_failed


router = APIRouter()


@router.get("/templates", response_model=List[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    items = db.query(Template).all()
    return [TemplateOut(**t.__dict__) for t in items]


@router.post("/templates", response_model=TemplateOut, dependencies=[Depends(require_permissions("communication.templates.create"))])
def create_template_endpoint(data: TemplateCreate, db: Session = Depends(get_db)):
    t = create_template(db, data)
    return TemplateOut(**t.__dict__)


@router.put("/templates/{template_id}", response_model=TemplateOut, dependencies=[Depends(require_permissions("communication.templates.update"))])
def update_template_endpoint(template_id: int, data: TemplateUpdate, db: Session = Depends(get_db)):
    t = db.query(Template).filter(Template.id == template_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    t = update_template(db, t, data)
    return TemplateOut(**t.__dict__)


@router.get("/queue", response_model=List[MessageOut])
def list_queue(status_: Optional[str] = Query(default=None, alias="status"), channel: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(MessageQueue)
    if status_:
        q = q.filter(MessageQueue.status == status_)
    if channel:
        q = q.filter(MessageQueue.channel == channel)
    items = q.all()
    return [MessageOut(**m.__dict__) for m in items]


@router.post("/send", response_model=MessageOut, dependencies=[Depends(require_permissions("communication.messages.enqueue"))])
def send_message_endpoint(data: MessageCreate, dispatch_now: bool = False, db: Session = Depends(get_db)):
    msg = enqueue_message(db, data)
    if dispatch_now:
        msg = dispatch_message(db, msg)
    return MessageOut(**msg.__dict__)


@router.post("/dispatch/{message_id}", response_model=MessageOut, dependencies=[Depends(require_permissions("communication.messages.dispatch"))])
def dispatch_message_endpoint(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(MessageQueue).filter(MessageQueue.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    msg = dispatch_message(db, msg)
    return MessageOut(**msg.__dict__)


@router.post("/requeue/{message_id}", response_model=MessageOut, dependencies=[Depends(require_permissions("communication.messages.requeue"))])
def requeue_message_endpoint(message_id: int, db: Session = Depends(get_db)):
    try:
        msg = requeue_failed(db, message_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return MessageOut(**msg.__dict__)


@router.get("/history", response_model=List[MessageOut])
def communication_history(
    contract_id: Optional[int] = Query(default=None),
    client_id: Optional[int] = Query(default=None),
    provider: Optional[str] = Query(default=None),
    status_: Optional[str] = Query(default=None, alias="status"),
    channel: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(MessageQueue)
    if contract_id:
        q = q.filter(MessageQueue.contract_id == contract_id)
    if client_id:
        q = q.filter(MessageQueue.client_id == client_id)
    if provider:
        q = q.filter(MessageQueue.provider == provider)
    if status_:
        q = q.filter(MessageQueue.status == status_)
    if channel:
        q = q.filter(MessageQueue.channel == channel)
    items = q.order_by(MessageQueue.created_at.desc()).limit(200).all()
    return [MessageOut(**m.__dict__) for m in items]


@router.post("/webhook/{provider}")
def communication_webhook(provider: str, payload: dict, db: Session = Depends(get_db)):
    prov = provider.lower()
    # Basic mapping: provider should send {"message_id":"...","status":"sent|failed"}
    message_id = payload.get("message_id")
    status_str = (payload.get("status") or "").lower()
    if not message_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing message_id")
    msg = db.query(MessageQueue).filter(MessageQueue.provider == prov, MessageQueue.provider_message_id == str(message_id)).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if status_str in ("delivered", "sent"):
        msg.status = "sent"
        msg.error = None
    elif status_str in ("failed", "undelivered"):
        msg.status = "failed"
        msg.error = payload.get("error") or msg.error
    else:
        msg.status = msg.status
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"ok": True}
