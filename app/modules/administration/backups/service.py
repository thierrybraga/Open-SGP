"""
Arquivo: app/modules/administration/backups/service.py

Responsabilidade:
Regras de negócio de Backups: criação de jobs e execução com gravação em disco.

Integrações:
- modules.administration.backups.models
"""

import os
from datetime import datetime
from sqlalchemy.orm import Session

from .models import BackupJob, BackupExecution
from .schemas import BackupJobCreate


def create_job(db: Session, data: BackupJobCreate) -> BackupJob:
    job = BackupJob(**data.dict())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def trigger_backup(db: Session, job: BackupJob) -> BackupExecution:
    exec_ = BackupExecution(job_id=job.id, status="running")
    db.add(exec_)
    db.commit()
    db.refresh(exec_)

    try:
        os.makedirs(job.storage_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"backup_{job.id}_{ts}.bak"
        path = os.path.join(job.storage_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Backup job {job.name} ({job.type}) at {ts}\n")
        exec_.status = "success"
        exec_.file_path = path
        exec_.finished_at = datetime.utcnow()
        exec_.error = None
    except Exception as e:
        exec_.status = "failed"
        exec_.finished_at = datetime.utcnow()
        exec_.error = str(e)

    db.add(exec_)
    db.commit()
    db.refresh(exec_)
    return exec_
