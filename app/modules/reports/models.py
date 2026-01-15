"""
Arquivo: app/modules/reports/models.py

Responsabilidade:
Modelos de Relatórios e Dashboards: definição de relatórios, widgets e logs de
execução, com campos configuráveis e auditáveis.

Integrações:
- core.database
- shared.models
"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


def JSONType():
    return JSON


class ReportDefinition(Base, TimestampMixin):
    __tablename__ = "report_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    query_type: Mapped[str] = mapped_column(String(20))  # aggregate, sql, orm
    parameters: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    logs = relationship("ReportExecutionLog", back_populates="report", cascade="all, delete-orphan")


class DashboardWidget(Base, TimestampMixin):
    __tablename__ = "dashboard_widgets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(60), unique=True)
    type: Mapped[str] = mapped_column(String(20))  # chart, table, metric
    config: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)
    position_row: Mapped[int] = mapped_column(Integer, default=0)
    position_col: Mapped[int] = mapped_column(Integer, default=0)
    size_x: Mapped[int] = mapped_column(Integer, default=1)
    size_y: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReportExecutionLog(Base, TimestampMixin):
    __tablename__ = "report_execution_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("report_definitions.id", ondelete="CASCADE"), index=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, failed
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rows_count: Mapped[int] = mapped_column(Integer, default=0)

    report = relationship("ReportDefinition", back_populates="logs")
