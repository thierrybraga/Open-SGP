"""
Arquivo: app/modules/administration/email_config/schemas.py

Responsabilidade:
Schemas Pydantic para Configuração de E-mail.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class EmailConfigurationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    use_tls: bool = True
    use_ssl: bool = False
    from_email: EmailStr
    from_name: str
    reply_to_email: Optional[EmailStr] = None
    max_emails_per_hour: Optional[int] = None
    max_emails_per_day: Optional[int] = None
    timeout: int = 30
    is_active: bool = True
    is_default: bool = False
    company_id: Optional[int] = None

    @field_validator('smtp_port')
    @classmethod
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError('smtp_port must be between 1 and 65535')
        return v

    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        if v < 1:
            raise ValueError('timeout must be at least 1 second')
        return v


class EmailConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    reply_to_email: Optional[EmailStr] = None
    max_emails_per_hour: Optional[int] = None
    max_emails_per_day: Optional[int] = None
    timeout: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class EmailConfigurationOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    smtp_host: str
    smtp_port: int
    smtp_user: str
    # smtp_password não é retornado por segurança
    use_tls: bool
    use_ssl: bool
    from_email: str
    from_name: str
    reply_to_email: Optional[str] = None
    max_emails_per_hour: Optional[int] = None
    max_emails_per_day: Optional[int] = None
    timeout: int
    is_active: bool
    is_default: bool
    last_test_at: Optional[str] = None
    last_test_success: Optional[bool] = None
    last_test_error: Optional[str] = None
    company_id: Optional[int] = None

    class Config:
        from_attributes = True


class EmailTestRequest(BaseModel):
    """Request para testar configuração de email."""
    to_email: EmailStr
    subject: str = "Teste de Configuração SMTP"
    body: str = "Este é um e-mail de teste para verificar a configuração do servidor SMTP."


class EmailTestResult(BaseModel):
    """Resultado do teste de email."""
    success: bool
    message: str
    error_detail: Optional[str] = None
