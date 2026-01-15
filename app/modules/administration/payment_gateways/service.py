"""
Arquivo: app/modules/administration/payment_gateways/service.py

Responsabilidade:
Lógica de negócio para Payment Gateways.
"""

from sqlalchemy.orm import Session

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

    # Implementação simplificada - em produção, fazer requisição real à API do provedor
    try:
        # Aqui seria feita uma requisição real de teste ao provedor
        # Por exemplo: para Pagar.me, fazer GET /1/status
        # Para MercadoPago, fazer GET /v1/users/me

        return {
            "success": True,
            "provider": gateway.provider,
            "environment": gateway.environment,
            "message": "Connection test successful (simulated)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
