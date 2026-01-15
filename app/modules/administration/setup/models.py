"""
Arquivo: app/modules/administration/setup/models.py

Responsabilidade:
Modelo de Setup para rastrear progresso do wizard de configuração inicial.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
import json

from ....core.database import Base
from ....shared.models import TimestampMixin


class SetupProgress(Base, TimestampMixin):
    """
    Rastreia o progresso da configuração inicial do sistema.
    """
    __tablename__ = "setup_progress"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Status geral
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    current_step: Mapped[int] = mapped_column(Integer, default=1)

    # Etapas individuais (1-7)
    company_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    financial_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    network_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    plans_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    contract_template_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    email_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    first_user_created: Mapped[bool] = mapped_column(Boolean, default=False)

    # Dados adicionais em JSON
    config_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Notas
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def get_config_data(self) -> dict:
        """Retorna dados de configuração como dict."""
        if self.config_data:
            try:
                return json.loads(self.config_data)
            except:
                return {}
        return {}

    def set_config_data(self, data: dict):
        """Define dados de configuração a partir de dict."""
        self.config_data = json.dumps(data)

    def get_progress_percentage(self) -> int:
        """Calcula percentual de progresso."""
        total_steps = 8
        completed_steps = sum([
            self.company_configured,
            self.financial_configured,
            self.network_configured,
            self.plans_configured,
            self.contract_template_configured,
            self.email_configured,
            self.monitoring_configured,
            self.first_user_created
        ])
        return int((completed_steps / total_steps) * 100)
