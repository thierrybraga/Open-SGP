"""
Arquivo: app/modules/discounts/routes.py

Responsabilidade:
Rotas REST para Descontos.

Integrações:
- core.dependencies
- modules.discounts.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date

from ...core.dependencies import get_db, require_permissions
from .models import PlanDiscount, PaymentMethodDiscount
from .schemas import (
    PlanDiscountCreate,
    PlanDiscountUpdate,
    PlanDiscountOut,
    PaymentMethodDiscountCreate,
    PaymentMethodDiscountUpdate,
    PaymentMethodDiscountOut,
    DiscountCalculation
)
from .service import (
    create_plan_discount,
    update_plan_discount,
    create_payment_method_discount,
    update_payment_method_discount,
    calculate_discounts_for_contract,
    get_active_plan_discounts,
    get_active_payment_method_discounts
)


router = APIRouter()


# ===== PLAN DISCOUNTS =====

@router.get("/plans", response_model=List[PlanDiscountOut])
def list_plan_discounts(
    plan_id: Optional[int] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista descontos por plano.
    """
    q = db.query(PlanDiscount)

    if plan_id is not None:
        q = q.filter(PlanDiscount.plan_id == plan_id)
    if is_active is not None:
        q = q.filter(PlanDiscount.is_active == is_active)

    discounts = q.order_by(PlanDiscount.created_at.desc()).all()
    return [PlanDiscountOut(**d.__dict__) for d in discounts]


@router.post("/plans", response_model=PlanDiscountOut, dependencies=[Depends(require_permissions("discounts.create"))])
def create_plan_discount_endpoint(
    data: PlanDiscountCreate,
    db: Session = Depends(get_db)
):
    """
    Cria desconto por plano.
    """
    # Verificar se já existe desconto ativo para o plano
    existing = db.query(PlanDiscount).filter(
        PlanDiscount.plan_id == data.plan_id,
        PlanDiscount.is_active == True
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active discount already exists for this plan"
        )

    discount = create_plan_discount(db, data)
    return PlanDiscountOut(**discount.__dict__)


@router.get("/plans/{discount_id}", response_model=PlanDiscountOut)
def get_plan_discount(discount_id: int, db: Session = Depends(get_db)):
    """
    Busca desconto por plano por ID.
    """
    discount = db.query(PlanDiscount).filter(PlanDiscount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")

    return PlanDiscountOut(**discount.__dict__)


@router.put("/plans/{discount_id}", response_model=PlanDiscountOut, dependencies=[Depends(require_permissions("discounts.update"))])
def update_plan_discount_endpoint(
    discount_id: int,
    data: PlanDiscountUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza desconto por plano.
    """
    discount = db.query(PlanDiscount).filter(PlanDiscount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")

    discount = update_plan_discount(db, discount, data)
    return PlanDiscountOut(**discount.__dict__)


@router.delete("/plans/{discount_id}", dependencies=[Depends(require_permissions("discounts.delete"))])
def delete_plan_discount(discount_id: int, db: Session = Depends(get_db)):
    """
    Remove desconto por plano.
    """
    discount = db.query(PlanDiscount).filter(PlanDiscount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")

    db.delete(discount)
    db.commit()

    return {"message": "Discount deleted successfully"}


# ===== PAYMENT METHOD DISCOUNTS =====

@router.get("/payment-methods", response_model=List[PaymentMethodDiscountOut])
def list_payment_method_discounts(
    payment_method: Optional[str] = Query(default=None),
    plan_id: Optional[int] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista descontos por forma de pagamento.
    """
    q = db.query(PaymentMethodDiscount)

    if payment_method is not None:
        q = q.filter(PaymentMethodDiscount.payment_method == payment_method)
    if plan_id is not None:
        q = q.filter((PaymentMethodDiscount.plan_id == plan_id) | (PaymentMethodDiscount.plan_id.is_(None)))
    if is_active is not None:
        q = q.filter(PaymentMethodDiscount.is_active == is_active)

    discounts = q.order_by(PaymentMethodDiscount.created_at.desc()).all()
    return [PaymentMethodDiscountOut(**d.__dict__) for d in discounts]


@router.post("/payment-methods", response_model=PaymentMethodDiscountOut, dependencies=[Depends(require_permissions("discounts.create"))])
def create_payment_method_discount_endpoint(
    data: PaymentMethodDiscountCreate,
    db: Session = Depends(get_db)
):
    """
    Cria desconto por forma de pagamento.
    """
    discount = create_payment_method_discount(db, data)
    return PaymentMethodDiscountOut(**discount.__dict__)


@router.get("/payment-methods/{discount_id}", response_model=PaymentMethodDiscountOut)
def get_payment_method_discount(discount_id: int, db: Session = Depends(get_db)):
    """
    Busca desconto por forma de pagamento por ID.
    """
    discount = db.query(PaymentMethodDiscount).filter(PaymentMethodDiscount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")

    return PaymentMethodDiscountOut(**discount.__dict__)


@router.put("/payment-methods/{discount_id}", response_model=PaymentMethodDiscountOut, dependencies=[Depends(require_permissions("discounts.update"))])
def update_payment_method_discount_endpoint(
    discount_id: int,
    data: PaymentMethodDiscountUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza desconto por forma de pagamento.
    """
    discount = db.query(PaymentMethodDiscount).filter(PaymentMethodDiscount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")

    discount = update_payment_method_discount(db, discount, data)
    return PaymentMethodDiscountOut(**discount.__dict__)


@router.delete("/payment-methods/{discount_id}", dependencies=[Depends(require_permissions("discounts.delete"))])
def delete_payment_method_discount(discount_id: int, db: Session = Depends(get_db)):
    """
    Remove desconto por forma de pagamento.
    """
    discount = db.query(PaymentMethodDiscount).filter(PaymentMethodDiscount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")

    db.delete(discount)
    db.commit()

    return {"message": "Discount deleted successfully"}


# ===== CALCULATION =====

@router.get("/calculate", response_model=DiscountCalculation)
def calculate_contract_discounts(
    plan_id: int = Query(...),
    payment_method: str = Query(...),
    amount: float = Query(...),
    contract_start_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Calcula descontos aplicáveis a um contrato.
    """
    return calculate_discounts_for_contract(
        db,
        plan_id,
        payment_method,
        amount,
        contract_start_date
    )
