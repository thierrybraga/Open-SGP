"""
Arquivo: app/modules/communication/service.py

Responsabilidade:
Regras de negócio para comunicação: gerenciar templates, enfileirar mensagens e
despachar (stub), reprocessar falhas e atualizar status.

Integrações:
- modules.communication.models
"""

from datetime import datetime
import os
from sqlalchemy.orm import Session
from .models import Template, MessageQueue
from .schemas import TemplateCreate, TemplateUpdate, MessageCreate
from .providers.email import send_email
from .providers.sms import send_sms
from .providers.whatsapp import send_whatsapp
from ...core.config import settings


def create_template(db: Session, data: TemplateCreate) -> Template:
    t = Template(**data.dict())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def update_template(db: Session, tpl: Template, data: TemplateUpdate) -> Template:
    for field, value in data.dict(exclude_none=True).items():
        setattr(tpl, field, value)
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


def enqueue_message(db: Session, data: MessageCreate) -> MessageQueue:
    msg = MessageQueue(**data.dict(), status="queued")
    db.add(msg)
    db.commit()
    db.refresh(msg)

    try:
        import redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.Redis.from_url(redis_url)
        r.lpush("comm_queue", str(msg.id))
    except Exception:
        pass

    return msg


def dispatch_message(db: Session, msg: MessageQueue) -> MessageQueue:
    try:
        sent_ok = True
        if msg.channel == "email":
            subject = "Mensagem"
            sent_ok = send_email(destination=msg.destination, subject=subject, content=msg.content)
        elif msg.channel == "sms":
            sent_ok = send_sms(destination=msg.destination, content=msg.content)
        elif msg.channel == "whatsapp":
            sent_ok = send_whatsapp(destination=msg.destination, content=msg.content)
            if sent_ok:
                msg.provider = msg.provider or "whatsapp_api"
                msg.provider_message_id = msg.provider_message_id or f"{msg.id}-{int(datetime.utcnow().timestamp())}"
        else:
            sent_ok = True
        msg.attempts = int(msg.attempts or 0) + 1
        msg.status = "sent" if sent_ok else "failed"
        msg.dispatched_at = datetime.utcnow()
        msg.error = None if sent_ok else (msg.error or "send failed")
        if not sent_ok:
            from datetime import timedelta
            backoff_seconds = min(60 * 60, 5 * (2 ** (msg.attempts - 1)))
            msg.next_attempt_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
    except Exception as e:
        msg.attempts = int(msg.attempts or 0) + 1
        msg.status = "failed"
        msg.error = str(e)
        msg.next_attempt_at = datetime.utcnow()
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg


def requeue_failed(db: Session, msg_id: int) -> MessageQueue:
    msg = db.query(MessageQueue).filter(MessageQueue.id == msg_id).first()
    if not msg:
        raise ValueError("Message not found")
    msg.status = "queued"
    msg.error = None
    msg.dispatched_at = None
    msg.next_attempt_at = datetime.utcnow()
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
