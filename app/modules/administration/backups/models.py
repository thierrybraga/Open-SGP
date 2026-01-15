"""
Arquivo: app/modules/administration/backups/models.py

Responsabilidade:
Modelos de Backups: definição de jobs e execuções com auditoria.

Integrações:
- core.database
- shared.models
"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ....core.database import Base
from ....shared.models import TimestampMixin


class BackupJob(Base, TimestampMixin):
    __tablename__ = "backup_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20))  # database, files
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)
    storage_dir: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    executions = relationship("BackupExecution", back_populates="job", cascade="all, delete-orphan")


class BackupExecution(Base, TimestampMixin):
    __tablename__ = "backup_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("backup_jobs.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="running")  # running, success, failed
    file_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    job = relationship("BackupJob", back_populates="executions")

    __table_args__ = (
        Index("ix_backup_exec_status", "status"),
    )
