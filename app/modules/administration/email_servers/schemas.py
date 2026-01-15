"""
Arquivo: app/modules/administration/email_servers/schemas.py

Responsabilidade:
Schemas Pydantic para Email Servers.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class EmailServerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    use_tls: bool = True
    use_ssl: bool = False
    from_email: EmailStr
    from_name: Optional[str] = None
    max_emails_per_hour: Optional[int] = None
    max_emails_per_day: Optional[int] = None
    is_active: bool = True
    is_default: bool = False

    @field_validator('smtp_port')
    @classmethod
    def validate_smtp_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('smtp_port must be between 1 and 65535')
        return v

    @field_validator('use_tls', 'use_ssl')
    @classmethod
    def validate_security(cls, v, info):
        # TLS e SSL não devem estar ativos simultaneamente
        if info.field_name == 'use_ssl' and v and info.data.get('use_tls'):
            raise ValueError('use_tls and use_ssl cannot both be true')
        return v


class EmailServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    max_emails_per_hour: Optional[int] = None
    max_emails_per_day: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class EmailServerOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    smtp_host: str
    smtp_port: int
    smtp_username: str
    # smtp_password não é retornado por segurança
    use_tls: bool
    use_ssl: bool
    from_email: str
    from_name: Optional[str] = None
    max_emails_per_hour: Optional[int] = None
    max_emails_per_day: Optional[int] = None
    is_active: bool
    is_default: bool
    emails_sent_today: int
    emails_sent_this_hour: int
    last_used_at: Optional[str] = None

    class Config:
        from_attributes = True


class EmailTestRequest(BaseModel):
    to_email: EmailStr
    subject: str = "Test Email from Open-SGP"
    body: str = "This is a test email to verify SMTP configuration."
