"""
Arquivo: app/workers/communication_worker.py

Responsabilidade:
Worker de comunicação: consome fila Redis e despacha mensagens da tabela
comm_message_queue.

Integrações:
- core.config
- core.database
- modules.communication
"""

import os
import time
import redis
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from ..core.config import settings
from ..modules.communication.models import MessageQueue
from ..modules.communication.service import dispatch_message


def main():
    r = redis.Redis.from_url(os.getenv("REDIS_URL", settings.redis_url))
    engine = create_engine(settings.effective_database_url, pool_pre_ping=True)
    while True:
        try:
            item = r.brpop("comm_queue", timeout=5)
            if not item:
                continue
            _, msg_id_bytes = item
            msg_id = int(msg_id_bytes.decode("utf-8"))
            db = Session(bind=engine)
            msg = db.query(MessageQueue).filter(MessageQueue.id == msg_id).first()
            if msg and msg.status == "queued":
                now_ts = __import__("datetime").datetime.utcnow()
                if msg.scheduled_at and msg.scheduled_at > now_ts:
                    # Re-enfileira para futura execução
                    r.lpush("comm_queue", str(msg.id))
                elif msg.next_attempt_at and msg.next_attempt_at > now_ts:
                    # Respeita backoff
                    r.lpush("comm_queue", str(msg.id))
                else:
                    try:
                        dispatch_message(db, msg)
                    except Exception as e:
                        msg.attempts = (msg.attempts or 0) + 1
                        msg.error = str(e)
                        if msg.attempts >= 5:
                            msg.status = "failed"
                            db.add(msg)
                            db.commit()
                            r.lpush("comm_dlq", str(msg.id))
                        else:
                            # Exponential backoff simples: 2^attempts minutos
                            delay_min = 2 ** msg.attempts
                            msg.next_attempt_at = now_ts + __import__("datetime").timedelta(minutes=delay_min)
                            db.add(msg)
                            db.commit()
                            r.lpush("comm_queue", str(msg.id))
            db.close()
        except Exception:
            time.sleep(1)


if __name__ == "__main__":
    main()
