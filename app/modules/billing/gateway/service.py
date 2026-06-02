"""
Arquivo: app/modules/billing/gateway/service.py

Responsabilidade:
Regras de negócio de gateway: criar configs, criar cobranças, atualizar status.

Integrações:
- modules.billing.gateway.models
- modules.billing.models
"""

from sqlalchemy.orm import Session
import requests

from .models import PaymentGatewayConfig, PaymentCharge
from ..models import Title
from ...clients.models import Client
from ...contracts.models import Contract
from ....shared.money import money


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

    reference = f"{cfg.provider}:{t.document_number or t.id}"
    external = _create_provider_charge(db, cfg, t, reference)

    ch = PaymentCharge(
        title_id=t.id,
        gateway_id=cfg.id,
        status=external.get("status", "created"),
        reference=reference,
        amount=t.amount,
        payment_url=external.get("payment_url"),
        external_id=external.get("external_id"),
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


def _create_provider_charge(db: Session, cfg: PaymentGatewayConfig, title: Title, reference: str) -> dict:
    provider = cfg.provider.lower()
    if provider == "asaas":
        return _create_asaas_charge(db, cfg, title, reference)
    if provider in ("gerencianet", "efi"):
        return _create_efi_charge(db, cfg, title, reference)
    raise ValueError(f"Unsupported payment gateway provider for homologation: {cfg.provider}")


def _title_client(db: Session, title: Title) -> Client:
    contract = db.query(Contract).filter(Contract.id == title.contract_id).first()
    if not contract:
        raise ValueError("Contract not found for title")
    client = db.query(Client).filter(Client.id == contract.client_id).first()
    if not client:
        raise ValueError("Client not found for title")
    return client


def _create_asaas_charge(db: Session, cfg: PaymentGatewayConfig, title: Title, reference: str) -> dict:
    if not cfg.api_key:
        raise ValueError("Asaas API key is required")

    client = _title_client(db, title)
    base_url = "https://sandbox.asaas.com/api/v3" if "sandbox" in cfg.provider.lower() else "https://api.asaas.com/v3"
    customer_id = _create_asaas_customer(cfg, client)
    payload = {
        "customer": customer_id,
        "billingType": "BOLETO",
        "value": float(money(title.amount)),
        "dueDate": title.due_date.isoformat(),
        "description": title.document_number or f"Titulo {title.id}",
        "externalReference": title.document_number or str(title.id),
    }
    response = requests.post(
        f"{base_url}/payments",
        json=payload,
        headers={"access_token": cfg.api_key, "Content-Type": "application/json"},
        timeout=30,
    )
    if response.status_code >= 400:
        raise ValueError(f"Asaas charge creation failed: {response.status_code} {response.text[:500]}")
    data = response.json()
    return {
        "status": str(data.get("status") or "created").lower(),
        "external_id": str(data.get("id")) if data.get("id") else None,
        "payment_url": data.get("invoiceUrl") or data.get("bankSlipUrl") or data.get("transactionReceiptUrl"),
    }


def _create_asaas_customer(cfg: PaymentGatewayConfig, client: Client) -> str:
    base_url = "https://sandbox.asaas.com/api/v3" if "sandbox" in cfg.provider.lower() else "https://api.asaas.com/v3"
    address = next((addr for addr in client.addresses if addr.is_primary), None) or (client.addresses[0] if client.addresses else None)
    payload = {
        "name": client.name,
        "cpfCnpj": "".join(filter(str.isdigit, client.document or "")),
        "email": client.email,
        "phone": "".join(filter(str.isdigit, client.phone or "")),
    }
    if address:
        payload.update(
            {
                "postalCode": "".join(filter(str.isdigit, address.zipcode or "")),
                "address": address.street,
                "addressNumber": address.number,
                "province": address.neighborhood,
            }
        )
    response = requests.post(
        f"{base_url}/customers",
        json=payload,
        headers={"access_token": cfg.api_key, "Content-Type": "application/json"},
        timeout=30,
    )
    if response.status_code >= 400:
        raise ValueError(f"Asaas customer creation failed: {response.status_code} {response.text[:500]}")
    data = response.json()
    if not data.get("id"):
        raise ValueError("Asaas customer creation did not return an id")
    return str(data["id"])


def _create_efi_charge(db: Session, cfg: PaymentGatewayConfig, title: Title, reference: str) -> dict:
    raise ValueError(
        "Efí/Gerencianet charge creation requires OAuth client_id/client_secret and certificate configuration; "
        "do not create local placeholder payment URLs for homologation."
    )


def update_charge_status(db: Session, charge: PaymentCharge, status: str, payment_url: str | None = None) -> PaymentCharge:
    charge.status = status
    if payment_url is not None:
        charge.payment_url = payment_url
    db.add(charge)
    db.commit()
    db.refresh(charge)
    return charge
