"""
Arquivo: app/modules/administration/payment_gateways/schemas.py

Responsabilidade:
Schemas Pydantic para Payment Gateways.
"""

from pydantic import BaseModel, field_validator
from typing import Optional


class PaymentGatewayCreate(BaseModel):
    name: str
    provider: str  # pagarme, mercadopago, asaas, stripe, etc
    payment_type: str  # pix, credit_card, boleto, debit_card
    credentials: dict  # Flexível para diferentes provedores
    settings: Optional[dict] = None
    environment: str = "sandbox"  # sandbox, production
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    notes: Optional[str] = None

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        valid_providers = ['pagarme', 'mercadopago', 'asaas', 'stripe', 'paypal', 'pagseguro', 'cielo', 'rede', 'getnet', 'stone', 'other']
        if v not in valid_providers:
            raise ValueError(f'provider must be one of {valid_providers}')
        return v

    @field_validator('payment_type')
    @classmethod
    def validate_payment_type(cls, v):
        valid_types = ['pix', 'credit_card', 'boleto', 'debit_card', 'bank_slip', 'wallet']
        if v not in valid_types:
            raise ValueError(f'payment_type must be one of {valid_types}')
        return v

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        if v not in ['sandbox', 'production']:
            raise ValueError('environment must be sandbox or production')
        return v


class PaymentGatewayUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    payment_type: Optional[str] = None
    credentials: Optional[dict] = None
    settings: Optional[dict] = None
    environment: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    notes: Optional[str] = None


class PaymentGatewayOut(BaseModel):
    id: int
    name: str
    provider: str
    payment_type: str
    credentials: dict  # Nota: Em produção, pode querer mascarar credenciais sensíveis
    settings: Optional[dict] = None
    environment: str
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_active: bool
    is_default: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True
