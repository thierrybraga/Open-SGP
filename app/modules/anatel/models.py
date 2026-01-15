"""
Arquivo: app/modules/anatel/models.py

Responsabilidade:
Modelos para armazenar histórico de relatórios ANATEL gerados.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base
from ...shared.models import TimestampMixin


class ANATELReport(Base, TimestampMixin):
    """
    Histórico de relatórios ANATEL gerados.
    """
    __tablename__ = "anatel_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    report_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # sici, ppp_scm
    reference_period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM
    reference_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reference_month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Dados do relatório
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Conteúdo do arquivo gerado

    # Metadados
    generated_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_status: Mapped[str] = mapped_column(String(20), default="completed")  # completed, error
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Estatísticas (específicas por tipo de relatório)
    stats_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON com estatísticas

    __table_args__ = ()
