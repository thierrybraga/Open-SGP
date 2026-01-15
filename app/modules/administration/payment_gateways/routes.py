"""
Arquivo: app/modules/administration/payment_gateways/routes.py

Responsabilidade:
Rotas REST para Payment Gateways.

Integrações:
- core.dependencies
- modules.administration.payment_gateways.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import PaymentGateway
from .schemas import PaymentGatewayCreate, PaymentGatewayUpdate, PaymentGatewayOut
from .service import create_payment_gateway, update_payment_gateway, get_default_gateway, test_gateway_connection


router = APIRouter()


@router.get("/", response_model=List[PaymentGatewayOut])
def list_payment_gateways(
    provider: Optional[str] = Query(default=None),
    payment_type: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista gateways de pagamento.
    """
    q = db.query(PaymentGateway)

    if provider:
        q = q.filter(PaymentGateway.provider == provider)
    if payment_type:
        q = q.filter(PaymentGateway.payment_type == payment_type)
    if is_active is not None:
        q = q.filter(PaymentGateway.is_active == is_active)

    gateways = q.order_by(PaymentGateway.created_at.desc()).all()
    return [PaymentGatewayOut(**g.__dict__) for g in gateways]


@router.post("/", response_model=PaymentGatewayOut, dependencies=[Depends(require_permissions("administration.payment_gateways.create"))])
def create_payment_gateway_endpoint(data: PaymentGatewayCreate, db: Session = Depends(get_db)):
    """
    Cria gateway de pagamento.
    """
    gateway = create_payment_gateway(db, data)
    return PaymentGatewayOut(**gateway.__dict__)


@router.get("/{gateway_id}", response_model=PaymentGatewayOut)
def get_payment_gateway(gateway_id: int, db: Session = Depends(get_db)):
    """
    Busca gateway de pagamento por ID.
    """
    gateway = db.query(PaymentGateway).filter(PaymentGateway.id == gateway_id).first()
    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment gateway not found")

    return PaymentGatewayOut(**gateway.__dict__)


@router.put("/{gateway_id}", response_model=PaymentGatewayOut, dependencies=[Depends(require_permissions("administration.payment_gateways.update"))])
def update_payment_gateway_endpoint(
    gateway_id: int,
    data: PaymentGatewayUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza gateway de pagamento.
    """
    gateway = db.query(PaymentGateway).filter(PaymentGateway.id == gateway_id).first()
    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment gateway not found")

    gateway = update_payment_gateway(db, gateway, data)
    return PaymentGatewayOut(**gateway.__dict__)


@router.delete("/{gateway_id}", dependencies=[Depends(require_permissions("administration.payment_gateways.delete"))])
def delete_payment_gateway(gateway_id: int, db: Session = Depends(get_db)):
    """
    Remove gateway de pagamento.
    """
    gateway = db.query(PaymentGateway).filter(PaymentGateway.id == gateway_id).first()
    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment gateway not found")

    db.delete(gateway)
    db.commit()

    return {"message": "Payment gateway deleted successfully"}


@router.get("/default/{payment_type}", response_model=PaymentGatewayOut)
def get_default_gateway_endpoint(payment_type: str, db: Session = Depends(get_db)):
    """
    Retorna gateway padrão para um tipo de pagamento.
    """
    gateway = get_default_gateway(db, payment_type)
    if not gateway:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No default gateway found for this payment type")

    return PaymentGatewayOut(**gateway.__dict__)


@router.post("/{gateway_id}/test", dependencies=[Depends(require_permissions("administration.payment_gateways.test"))])
def test_gateway_connection_endpoint(gateway_id: int, db: Session = Depends(get_db)):
    """
    Testa conexão com o gateway de pagamento.
    """
    result = test_gateway_connection(db, gateway_id)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Connection test failed"))

    return result
