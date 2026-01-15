"""
Arquivo: app/modules/communication/worker.py

Responsabilidade:
Processa assincronamente mensagens de comunicação usando Redis e banco de dados,
respeitando next_attempt_at e filas, com despacho por canal.

Integrações:
- core.config
- modules.communication.models
- modules.communication.service
"""

import os
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from ...core.config import settings
from .models import MessageQueue
from .service import dispatch_message


def run_worker(sleep_seconds: int = 2):
    engine = create_engine(settings.effective_database_url, pool_pre_ping=True)
    db = Session(bind=engine)
    r = None
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url)
    except Exception:
        r = None

    try:
        while True:
            try:
                if r is not None:
                    item = r.brpop("comm_queue", timeout=1)
                    if item is not None:
                        _, msg_id_bytes = item
                        try:
                            msg_id = int(msg_id_bytes.decode("utf-8"))
                        except Exception:
                            msg_id = None
                        if msg_id:
                            msg = db.query(MessageQueue).filter(MessageQueue.id == msg_id).first()
                            if msg and msg.status == "queued":
                                dispatch_message(db, msg)
                now = datetime.utcnow()
                pending = (
                    db.query(MessageQueue)
                    .filter(MessageQueue.status == "queued")
                    .filter((MessageQueue.next_attempt_at.is_(None)) | (MessageQueue.next_attempt_at <= now))
                    .order_by(MessageQueue.created_at.asc())
                    .limit(10)
                    .all()
                )
                for msg in pending:
                    dispatch_message(db, msg)
            except Exception:
                pass
            time.sleep(sleep_seconds)
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    run_worker()
