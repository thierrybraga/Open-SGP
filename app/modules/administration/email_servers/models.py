"""
Arquivo: app/modules/administration/email_servers/models.py

Responsabilidade:
Modelo de Servidor de E-mail SMTP para envio de mensagens.

Integrações:
- core.database
- shared.models
- core.encryption (criptografia de senha)
"""

from sqlalchemy import String, Boolean, Integer, event
from sqlalchemy.orm import Mapped, mapped_column

from ....core.database import Base
from ....shared.models import TimestampMixin
from ....core.encryption import encrypt_password, decrypt_password, is_encrypted


class EmailServer(Base, TimestampMixin):
    """
    Configuração de servidor SMTP para envio de e-mails.
    """
    __tablename__ = "email_servers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Identificação
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Configurações SMTP
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_username: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_password: Mapped[str] = mapped_column(String(500), nullable=False)  # Criptografado com Fernet

    # Segurança
    use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=False)

    # Remetente padrão
    from_email: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Limites
    max_emails_per_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_emails_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Estatísticas (atualizadas por processo de envio)
    emails_sent_today: Mapped[int] = mapped_column(Integer, default=0)
    emails_sent_this_hour: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    def set_password(self, plaintext_password: str):
        """
        Define senha SMTP criptografada.

        Args:
            plaintext_password: Senha em texto plano
        """
        self.smtp_password = encrypt_password(plaintext_password)

    def get_password(self) -> str:
        """
        Retorna senha SMTP descriptografada.

        Returns:
            str: Senha em texto plano

        Note:
            Se a senha não estiver criptografada (legacy), retorna como está.
        """
        if not self.smtp_password:
            return ""

        # Se já está criptografada com Fernet, descriptografar
        if is_encrypted(self.smtp_password):
            return decrypt_password(self.smtp_password)

        # Se não está criptografada (legacy ou desenvolvimento), retornar como está
        return self.smtp_password


# Event listener para criptografar senha automaticamente antes de salvar
@event.listens_for(EmailServer, 'before_insert')
@event.listens_for(EmailServer, 'before_update')
def encrypt_password_before_save(mapper, connection, target):
    """
    Event listener que criptografa a senha automaticamente antes de salvar.

    Só criptografa se a senha ainda não estiver criptografada.
    """
    if target.smtp_password and not is_encrypted(target.smtp_password):
        target.smtp_password = encrypt_password(target.smtp_password)
