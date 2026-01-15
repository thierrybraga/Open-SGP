"""
Arquivo: app/modules/administration/backups/routes.py

Responsabilidade:
Rotas REST para Backups: CRUD de jobs e execução manual de backup.

Integrações:
- core.dependencies
- modules.administration.backups.service
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import BackupJob, BackupExecution
from .schemas import BackupJobCreate, BackupJobOut, BackupExecutionOut
from .service import create_job, trigger_backup


router = APIRouter()


@router.get("/jobs", response_model=List[BackupJobOut])
def list_jobs(db: Session = Depends(get_db)):
    items = db.query(BackupJob).all()
    return [BackupJobOut(**i.__dict__) for i in items]


@router.post("/jobs", response_model=BackupJobOut, dependencies=[Depends(require_permissions("admin.backups.create"))])
def create_job_endpoint(data: BackupJobCreate, db: Session = Depends(get_db)):
    job = create_job(db, data)
    return BackupJobOut(**job.__dict__)


@router.get("/executions", response_model=List[BackupExecutionOut])
def list_executions(db: Session = Depends(get_db)):
    items = db.query(BackupExecution).order_by(BackupExecution.started_at.desc()).limit(200).all()
    return [BackupExecutionOut(**{
        **e.__dict__,
        "started_at": e.started_at.isoformat(),
        "finished_at": e.finished_at.isoformat() if e.finished_at else None,
    }) for e in items]


@router.post("/jobs/{job_id}/run", response_model=BackupExecutionOut, dependencies=[Depends(require_permissions("admin.backups.trigger"))])
def run_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(BackupJob).filter(BackupJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup job not found")
    exec_ = trigger_backup(db, job)
    return BackupExecutionOut(**{
        **exec_.__dict__,
        "started_at": exec_.started_at.isoformat(),
        "finished_at": exec_.finished_at.isoformat() if exec_.finished_at else None,
    })
