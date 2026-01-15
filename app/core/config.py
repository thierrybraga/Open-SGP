"""
Arquivo: app/core/config.py

Responsabilidade:
Gerencia configurações da aplicação via variáveis de ambiente, incluindo URL do banco,
parâmetros de segurança, Redis e CORS.

Integrações:
- core.database
- core.security
- modules.*
"""

import os
from pydantic import BaseModel, validator, ValidationError
from typing import List


class Settings(BaseModel):
    app_name: str = "ISP ERP API"
    environment: str = os.getenv("ENVIRONMENT", "development")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    @validator('secret_key')
    def validate_secret_key(cls, v, values):
        """
        Valida SECRET_KEY em produção.

        Em produção, a SECRET_KEY NÃO PODE ser o valor padrão 'change-me'.
        Deve ter no mínimo 32 caracteres para segurança adequada.
        """
        environment = values.get('environment', 'development')

        if environment == 'production':
            if v == 'change-me':
                raise ValueError(
                    "SECRET_KEY cannot be 'change-me' in production! "
                    "Generate a strong key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )

            if len(v) < 32:
                raise ValueError(
                    f"SECRET_KEY too short in production ({len(v)} chars). "
                    "Must be at least 32 characters for adequate security."
                )

        return v

    @validator('environment')
    def validate_environment(cls, v):
        """Valida que environment é um valor válido"""
        valid_environments = ['development', 'production', 'testing', 'staging']
        if v not in valid_environments:
            raise ValueError(
                f"Invalid ENVIRONMENT '{v}'. "
                f"Must be one of: {', '.join(valid_environments)}"
            )
        return v

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/isp_erp",
    )

    testing_database_url: str = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///./isp_erp_test.db",
    )

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    cors_allow_origins: List[str] = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")

    @validator('cors_allow_origins')
    def validate_cors(cls, v, values):
        """
        Valida configuração de CORS em produção.

        Em produção, CORS não deve aceitar todas as origens (*).
        Deve especificar domínios específicos.
        """
        environment = values.get('environment', 'development')

        if environment == 'production':
            if "*" in v:
                raise ValueError(
                    "CORS_ALLOW_ORIGINS cannot be '*' (all origins) in production! "
                    "Specify allowed domains explicitly, e.g.: https://yourdomain.com"
                )

        return v

    # SMTP settings for communication providers
    smtp_host: str = os.getenv("SMTP_HOST", "localhost")
    smtp_port: int = int(os.getenv("SMTP_PORT", "25"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

    # SMS gateway configuration
    sms_gateway_url: str = os.getenv("SMS_GATEWAY_URL", "")
    sms_api_key: str = os.getenv("SMS_API_KEY", "")

    # WhatsApp gateway configuration
    whatsapp_gateway_url: str = os.getenv("WHATSAPP_GATEWAY_URL", "")
    whatsapp_api_token: str = os.getenv("WHATSAPP_API_TOKEN", "")
    whatsapp_provider: str = os.getenv("WHATSAPP_PROVIDER", "gateway")  # gateway, twilio, gupshup, zenvia
    # Twilio WhatsApp
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_number: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    # Gupshup WhatsApp
    gupshup_api_url: str = os.getenv("GUPSHUP_API_URL", "")
    gupshup_api_key: str = os.getenv("GUPSHUP_API_KEY", "")
    # Zenvia WhatsApp
    zenvia_api_url: str = os.getenv("ZENVIA_API_URL", "")
    zenvia_api_token: str = os.getenv("ZENVIA_API_TOKEN", "")

    # Fiscal certificate A1 (PFX) configuration
    a1_cert_pfx_path: str = os.getenv("A1_CERT_PFX_PATH", "")
    a1_cert_password: str = os.getenv("A1_CERT_PASSWORD", "")

    # Sentry monitoring
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    sentry_environment: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    sentry_traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")  # json or text

    # Feature flags
    feature_2fa_enabled: bool = os.getenv("FEATURE_2FA_ENABLED", "false").lower() == "true"
    feature_2fa_required_admin: bool = os.getenv("FEATURE_2FA_REQUIRED_ADMIN", "false").lower() == "true"

    # Token blacklist (logout) TTL in seconds
    token_blacklist_ttl: int = int(os.getenv("TOKEN_BLACKLIST_TTL", str(60 * 60 * 24)))  # 24 hours

    class Config:
        arbitrary_types_allowed = True

    @property
    def effective_database_url(self) -> str:
        if self.environment == "testing":
            return self.testing_database_url
        return self.database_url

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"

    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self.environment == "testing"


settings = Settings()
