"""
Arquivo: app/modules/administration/backups/schemas.py

Responsabilidade:
Esquemas Pydantic para Jobs de Backup e Execuções.

Integrações:
- modules.administration.backups.models
"""

from typing import Optional
from pydantic import BaseModel


class BackupJobCreate(BaseModel):
    name: str
    type: str
    schedule_cron: Optional[str] = None
    storage_dir: str
    is_active: bool = True


class BackupJobOut(BaseModel):
    id: int
    name: str
    type: str
    schedule_cron: Optional[str]
    storage_dir: str
    is_active: bool

    class Config:
        from_attributes = True


class BackupExecutionOut(BaseModel):
    id: int
    job_id: int
    started_at: str
    finished_at: Optional[str]
    status: str
    file_path: Optional[str]
    error: Optional[str]

    class Config:
        from_attributes = True
