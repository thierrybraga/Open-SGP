"""
Arquivo: app/modules/administration/payment_gateways/service.py

Responsabilidade:
Lógica de negócio para Payment Gateways.
"""

from sqlalchemy.orm import Session
import requests

from .models import PaymentGateway
from .schemas import PaymentGatewayCreate, PaymentGatewayUpdate


def create_payment_gateway(db: Session, data: PaymentGatewayCreate) -> PaymentGateway:
    """
    Cria um gateway de pagamento.
    """
    # Se for marcado como padrão, desmarcar outros
    if data.is_default:
        db.query(PaymentGateway).filter(
            PaymentGateway.payment_type == data.payment_type,
            PaymentGateway.is_default == True
        ).update({"is_default": False})

    gateway = PaymentGateway(**data.dict())
    db.add(gateway)
    db.commit()
    db.refresh(gateway)
    return gateway


def update_payment_gateway(db: Session, gateway: PaymentGateway, data: PaymentGatewayUpdate) -> PaymentGateway:
    """
    Atualiza um gateway de pagamento.
    """
    update_data = data.dict(exclude_none=True)

    # Se está marcando como padrão, desmarcar outros
    if update_data.get('is_default') == True:
        db.query(PaymentGateway).filter(
            PaymentGateway.payment_type == gateway.payment_type,
            PaymentGateway.id != gateway.id,
            PaymentGateway.is_default == True
        ).update({"is_default": False})

    for field, value in update_data.items():
        setattr(gateway, field, value)

    db.add(gateway)
    db.commit()
    db.refresh(gateway)
    return gateway


def get_default_gateway(db: Session, payment_type: str) -> PaymentGateway | None:
    """
    Retorna o gateway padrão para um tipo de pagamento.
    """
    return db.query(PaymentGateway).filter(
        PaymentGateway.payment_type == payment_type,
        PaymentGateway.is_default == True,
        PaymentGateway.is_active == True
    ).first()


def test_gateway_connection(db: Session, gateway_id: int) -> dict:
    """
    Testa a conexão com o gateway de pagamento.
    Retorna status de conexão.
    """
    gateway = db.query(PaymentGateway).filter(PaymentGateway.id == gateway_id).first()
    if not gateway:
        return {"success": False, "error": "Gateway not found"}

    try:
        return _test_provider_connection(gateway)
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _test_provider_connection(gateway: PaymentGateway) -> dict:
    provider = gateway.provider.lower()
    if provider == "asaas":
        return _test_asaas(gateway)
    if provider == "mercadopago":
        return _test_mercadopago(gateway)
    if provider == "stripe":
        return _test_stripe(gateway)
    raise ValueError(f"Provider {gateway.provider} does not have a real connection test implemented")


def _credential(gateway: PaymentGateway, *names: str) -> str:
    credentials = gateway.credentials or {}
    for name in names:
        value = credentials.get(name)
        if value:
            return str(value)
    raise ValueError(f"Missing credential: one of {', '.join(names)}")


def _test_asaas(gateway: PaymentGateway) -> dict:
    api_key = _credential(gateway, "api_key", "access_token")
    base_url = "https://sandbox.asaas.com/api/v3" if gateway.environment == "sandbox" else "https://api.asaas.com/v3"
    response = requests.get(f"{base_url}/myAccount", headers={"access_token": api_key}, timeout=15)
    return _gateway_response(gateway, response)


def _test_mercadopago(gateway: PaymentGateway) -> dict:
    token = _credential(gateway, "access_token", "api_key")
    response = requests.get("https://api.mercadopago.com/users/me", headers={"Authorization": f"Bearer {token}"}, timeout=15)
    return _gateway_response(gateway, response)


def _test_stripe(gateway: PaymentGateway) -> dict:
    api_key = _credential(gateway, "secret_key", "api_key")
    response = requests.get("https://api.stripe.com/v1/account", auth=(api_key, ""), timeout=15)
    return _gateway_response(gateway, response)


def _gateway_response(gateway: PaymentGateway, response: requests.Response) -> dict:
    if response.status_code >= 400:
        return {
            "success": False,
            "provider": gateway.provider,
            "environment": gateway.environment,
            "status_code": response.status_code,
            "error": response.text[:500],
        }
    return {
        "success": True,
        "provider": gateway.provider,
        "environment": gateway.environment,
        "status_code": response.status_code,
        "message": "Connection test successful",
    }
