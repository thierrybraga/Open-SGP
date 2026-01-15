"""
Arquivo: app/modules/administration/email_config/models.py

Responsabilidade:
Modelo de Configuração de Servidor de E-mail SMTP.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ....core.database import Base
from ....shared.models import TimestampMixin


class EmailConfiguration(Base, TimestampMixin):
    """
    Configuração de servidor SMTP para envio de e-mails.
    """
    __tablename__ = "email_configurations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Identificação
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Configuração SMTP
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_password: Mapped[str] = mapped_column(String(255), nullable=False)  # Criptografado

    # Segurança
    use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=False)

    # Remetente padrão
    from_email: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[str] = mapped_column(String(150), nullable=False)

    # Reply-to (opcional)
    reply_to_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Limite de envio
    max_emails_per_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_emails_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Configurações adicionais
    timeout: Mapped[int] = mapped_column(Integer, default=30)  # segundos

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Testes
    last_test_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_test_success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_test_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Associação com empresa (opcional)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)

    company = relationship("Company")
