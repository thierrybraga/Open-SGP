"""
Arquivo: app/modules/administration/setup/schemas.py

Responsabilidade:
Schemas para wizard de setup inicial.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class CompanySetup(BaseModel):
    """Etapa 1: Configuração da empresa."""
    name: str
    legal_name: str
    document: str  # CNPJ
    email: EmailStr
    phone: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class FinancialSetup(BaseModel):
    """Etapa 2: Configuração financeira."""
    carrier_name: str
    bank_code: str
    agency: str
    account: str
    wallet: str
    fine_percent: float = 2.0
    interest_percent: float = 1.0
    cnab_layout: str = "400"


class NetworkSetup(BaseModel):
    """Etapa 3: Configuração de rede."""
    pop_name: str
    pop_city: str
    pop_address: str
    pop_latitude: float
    pop_longitude: float
    nas_name: str
    nas_ip: str
    nas_secret: str
    nas_vendor: str = "MikroTik"


class PlanSetup(BaseModel):
    """Etapa 4: Primeiro plano."""
    name: str
    description: str
    download_speed_mbps: float
    upload_speed_mbps: float
    price: float
    category: str = "internet"


class ContractTemplateSetup(BaseModel):
    """Etapa 5: Template de contrato."""
    name: str
    content: str
    is_default: bool = True


class EmailSetup(BaseModel):
    """Etapa 6: Servidor de email."""
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool = True
    from_email: EmailStr
    from_name: str


class MonitoringSetup(BaseModel):
    """Etapa: Monitoramento (Zabbix)."""
    url: str
    user: str
    password: str
    enable_monitoring: bool = True


class FirstUserSetup(BaseModel):
    """Etapa 7: Primeiro usuário administrador."""
    username: str
    email: EmailStr
    full_name: str
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class SetupProgressOut(BaseModel):
    """Retorna progresso do setup."""
    id: int
    is_completed: bool
    current_step: int
    company_configured: bool
    financial_configured: bool
    network_configured: bool
    plans_configured: bool
    contract_template_configured: bool
    email_configured: bool
    monitoring_configured: bool
    first_user_created: bool
    progress_percentage: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class CompleteSetupRequest(BaseModel):
    """Request completa para setup em uma chamada."""
    company: CompanySetup
    financial: FinancialSetup
    network: NetworkSetup
    plan: PlanSetup
    contract_template: ContractTemplateSetup
    email: EmailSetup
    monitoring: MonitoringSetup
    first_user: FirstUserSetup
