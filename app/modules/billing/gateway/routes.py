"""
Arquivo: app/modules/billing/gateway/routes.py

Responsabilidade:
Rotas REST para gateway de pagamento: configs e cobranças.

Integrações:
- core.dependencies
- modules.billing.gateway.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import PaymentGatewayConfig, PaymentCharge
from .schemas import GatewayConfigCreate, GatewayConfigOut, ChargeCreate, ChargeOut, ChargeStatusUpdate
from .service import create_config, create_charge, update_charge_status


router = APIRouter()


@router.get("/configs", response_model=List[GatewayConfigOut])
def list_configs(db: Session = Depends(get_db)):
    items = db.query(PaymentGatewayConfig).all()
    return [GatewayConfigOut(**i.__dict__) for i in items]


@router.post(
    "/configs",
    response_model=GatewayConfigOut,
    dependencies=[Depends(require_permissions("billing.gateway.config.create"))],
)
def create_config_endpoint(data: GatewayConfigCreate, db: Session = Depends(get_db)):
    cfg = create_config(db, data.provider, data.api_key, data.enabled)
    return GatewayConfigOut(**cfg.__dict__)


@router.get("/charges", response_model=List[ChargeOut])
def list_charges(status_: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(PaymentCharge)
    if status_:
        q = q.filter(PaymentCharge.status == status_)
    items = q.order_by(PaymentCharge.created_at.desc()).all()
    return [ChargeOut(**i.__dict__) for i in items]


@router.post(
    "/charges",
    response_model=ChargeOut,
    dependencies=[Depends(require_permissions("billing.gateway.charge.create"))],
)
def create_charge_endpoint(data: ChargeCreate, db: Session = Depends(get_db)):
    try:
        ch = create_charge(db, data.title_id, data.provider)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ChargeOut(**ch.__dict__)


@router.put(
    "/charges/{charge_id}",
    response_model=ChargeOut,
    dependencies=[Depends(require_permissions("billing.gateway.charge.update"))],
)
def update_charge_status_endpoint(charge_id: int, data: ChargeStatusUpdate, db: Session = Depends(get_db)):
    ch = db.query(PaymentCharge).filter(PaymentCharge.id == charge_id).first()
    if not ch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found")
    ch = update_charge_status(db, ch, data.status, data.payment_url)
    return ChargeOut(**ch.__dict__)
