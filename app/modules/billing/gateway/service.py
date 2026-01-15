"""
Arquivo: app/modules/billing/gateway/service.py

Responsabilidade:
Regras de negócio de gateway: criar configs, criar cobranças, atualizar status.

Integrações:
- modules.billing.gateway.models
- modules.billing.models
"""

from sqlalchemy.orm import Session

from .models import PaymentGatewayConfig, PaymentCharge
from ..models import Title


def create_config(db: Session, provider: str, api_key: str, enabled: bool = True) -> PaymentGatewayConfig:
    cfg = PaymentGatewayConfig(provider=provider, api_key=api_key, enabled=enabled)
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


def create_charge(db: Session, title_id: int, provider: str | None = None) -> PaymentCharge:
    t = db.query(Title).filter(Title.id == title_id).first()
    if not t:
        raise ValueError("Title not found")
    if t.status != "open":
        raise ValueError("Title must be open to charge")

    cfg_q = db.query(PaymentGatewayConfig).filter(PaymentGatewayConfig.enabled == True)  # noqa: E712
    if provider:
        cfg_q = cfg_q.filter(PaymentGatewayConfig.provider == provider)
    cfg = cfg_q.first()
    if not cfg:
        raise ValueError("No enabled gateway configuration found")

    reference = f"{cfg.provider}:{t.document_number}"
    payment_url = f"https://pay.example.com/{cfg.provider}/{t.document_number}"

    ch = PaymentCharge(
        title_id=t.id,
        gateway_id=cfg.id,
        status="created",
        reference=reference,
        amount=t.amount,
        payment_url=payment_url,
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


def update_charge_status(db: Session, charge: PaymentCharge, status: str, payment_url: str | None = None) -> PaymentCharge:
    charge.status = status
    if payment_url is not None:
        charge.payment_url = payment_url
    db.add(charge)
    db.commit()
    db.refresh(charge)
    return charge
