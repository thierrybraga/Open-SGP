"""
Arquivo: app/workers/backup_worker.py

Responsabilidade:
Worker de agendamento de backups: lê jobs ativos com schedule_cron e executa
conforme cron simples (minutos) ou enfileira.

Integrações:
- core.config
- core.database
- modules.administration.backups.service
- modules.administration.backups.models
"""

import time
from datetime import datetime

try:
    import redis  # type: ignore
except Exception:
    redis = None  # fallback sem Redis

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from ..core.config import settings
from ..app.core.database import Base  # type: ignore
from ..modules.administration.backups.models import BackupJob
from ..modules.administration.backups.service import trigger_backup


def _due_minute(cron: str, dt: datetime) -> bool:
    # Suporta padrões: "* * * * *" (cada minuto) e "*/N * * * *" (a cada N minutos) e "M * * * *" (no minuto M)
    parts = cron.strip().split()
    if len(parts) != 5:
        return False
    minute = parts[0]
    m = dt.minute
    if minute == "*":
        return True
    if minute.startswith("*/"):
        try:
            n = int(minute[2:])
            return n > 0 and m % n == 0
        except Exception:
            return False
    try:
        return int(minute) == m
    except Exception:
        return False


def run_loop(poll_seconds: int = 30):
    engine = create_engine(settings.effective_database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)

    last_run_minute: dict[int, int] = {}
    queue = None
    if redis is not None:
        try:
            queue = redis.Redis.from_url(settings.redis_url)
        except Exception:
            queue = None

    while True:
        now = datetime.utcnow()
        minute = now.minute
        jobs = db.query(BackupJob).filter(BackupJob.is_active == True, BackupJob.schedule_cron != None).all()
        for job in jobs:
            cron = job.schedule_cron or ""
            if _due_minute(cron, now):
                if last_run_minute.get(job.id) == minute:
                    continue
                last_run_minute[job.id] = minute
                if queue:
                    try:
                        queue.lpush("backup_jobs_queue", job.id)
                    except Exception:
                        trigger_backup(db, job)
                else:
                    trigger_backup(db, job)
        time.sleep(poll_seconds)


if __name__ == "__main__":
    run_loop()
