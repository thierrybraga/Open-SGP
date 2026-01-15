"""
Arquivo: app/modules/billing/gateway/webhooks.py

Responsabilidade:
Endpoints de webhook para provedores (Asaas, GerenciaNet) e reconciliação
automática com PaymentCharge e Title.

Integrações:
- core.dependencies
- modules.billing.gateway.service
- modules.billing.gateway.models
- modules.billing.models
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ....core.dependencies import get_db
from .models import PaymentCharge, PaymentGatewayConfig
from ..models import Title, Payment
from .service import update_charge_status
import hmac
import hashlib
from datetime import datetime


router = APIRouter()


def _find_charge_by_reference(db: Session, provider: str, reference: str | None) -> PaymentCharge | None:
    if not reference:
        return None
    return db.query(PaymentCharge).filter(PaymentCharge.reference == f"{provider}:{reference}").first()


@router.post("/webhook/{provider}")
async def webhook_provider(provider: str, request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    payload = await request.json()
    # Asaas example: {"event":"PAYMENT_RECEIVED","payment":{"id":"pay_123","status":"RECEIVED","value":99.9,"billingType":"BOLETO","externalReference":"DOC-..."}}
    # GerenciaNet example: {"notification":{"id":"notif_123"},"charge":{"status":"paid","charge_id":321,"custom_id":"DOC-..."}}
    status_map = {
        "asaas": {
            "extract": lambda p: (
                (p.get("payment") or {}).get("externalReference"),
                (p.get("payment") or {}).get("status"),
            )
        },
        "gerencianet": {
            "extract": lambda p: (
                (p.get("charge") or {}).get("custom_id"),
                (p.get("charge") or {}).get("status"),
            )
        },
    }

    provider_key = provider.lower()
    if provider_key not in status_map:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")

    cfg = db.query(PaymentGatewayConfig).filter(PaymentGatewayConfig.provider == provider_key, PaymentGatewayConfig.enabled == True).first()  # noqa: E712
    if cfg and cfg.webhook_secret:
        sig = request.headers.get("X-Signature") or request.headers.get("X-Hub-Signature") or ""
        algo = cfg.hmac_algorithm.lower()
        dig = hmac.new(cfg.webhook_secret.encode("utf-8"), raw, getattr(hashlib, algo)).hexdigest()
        if sig.replace(f"{algo}=", "") != dig:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    reference, status_str = status_map[provider_key]["extract"](payload)
    ch = _find_charge_by_reference(db, provider_key, reference)
    if not ch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found")

    normalized = status_str.lower() if isinstance(status_str, str) else ""
    if normalized in ("received", "paid"):
        amount = None
        method = "boleto"
        external_id = None
        paid_at = None
        if provider_key == "asaas":
            pm = payload.get("payment") or {}
            amount = float(pm.get("value", 0) or 0)
            method = (pm.get("billingType") or "boleto").lower()
            external_id = pm.get("id")
            paid_at = pm.get("paymentDate") or pm.get("clientPaymentDate")
        elif provider_key == "gerencianet":
            chg = payload.get("charge") or {}
            amount = float(chg.get("value", 0) or 0)
            method = "boleto"
            external_id = chg.get("charge_id") or chg.get("id")
            paid_at = chg.get("paid_at")
        ch = update_charge_status(db, ch, "paid")
        if external_id and not ch.external_id:
            ch.external_id = str(external_id)
        if paid_at and not ch.paid_at:
            try:
                ch.paid_at = datetime.fromisoformat(str(paid_at))
            except Exception:
                ch.paid_at = datetime.utcnow()
        db.add(ch)
        t = db.query(Title).filter(Title.id == ch.title_id).first()
        if t and t.status != "paid":
            pay = Payment(title_id=t.id, payment_date=None, amount=amount or t.amount, method=method)
            db.add(pay)
            t.status = "paid"
            db.add(t)
            db.commit()
    elif normalized in ("canceled", "cancelled"):
        update_charge_status(db, ch, "canceled")
    else:
        update_charge_status(db, ch, normalized or "created")

    return {"ok": True}
