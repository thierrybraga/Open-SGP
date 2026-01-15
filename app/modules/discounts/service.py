"""
Arquivo: app/modules/discounts/service.py

Responsabilidade:
Lógica de negócio para Descontos.
"""

from sqlalchemy.orm import Session
from datetime import date
from dateutil.relativedelta import relativedelta

from .models import PlanDiscount, PaymentMethodDiscount
from .schemas import (
    PlanDiscountCreate,
    PlanDiscountUpdate,
    PaymentMethodDiscountCreate,
    PaymentMethodDiscountUpdate,
    DiscountCalculation
)


# ===== PLAN DISCOUNTS =====

def create_plan_discount(db: Session, data: PlanDiscountCreate) -> PlanDiscount:
    """
    Cria desconto por plano.
    """
    discount = PlanDiscount(**data.dict())
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


def update_plan_discount(db: Session, discount: PlanDiscount, data: PlanDiscountUpdate) -> PlanDiscount:
    """
    Atualiza desconto por plano.
    """
    for field, value in data.dict(exclude_none=True).items():
        setattr(discount, field, value)

    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


# ===== PAYMENT METHOD DISCOUNTS =====

def create_payment_method_discount(db: Session, data: PaymentMethodDiscountCreate) -> PaymentMethodDiscount:
    """
    Cria desconto por forma de pagamento.
    """
    discount = PaymentMethodDiscount(**data.dict())
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


def update_payment_method_discount(db: Session, discount: PaymentMethodDiscount, data: PaymentMethodDiscountUpdate) -> PaymentMethodDiscount:
    """
    Atualiza desconto por forma de pagamento.
    """
    for field, value in data.dict(exclude_none=True).items():
        setattr(discount, field, value)

    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


# ===== CALCULATION =====

def calculate_discount(amount: float, discount_type: str, discount_value: float) -> float:
    """
    Calcula valor do desconto.
    """
    if discount_type == "percentage":
        return amount * (discount_value / 100.0)
    elif discount_type == "fixed":
        return min(discount_value, amount)  # Desconto não pode ser maior que o valor
    return 0.0


def calculate_discounts_for_contract(
    db: Session,
    plan_id: int,
    payment_method: str,
    amount: float,
    contract_start_date: date = None
) -> DiscountCalculation:
    """
    Calcula todos os descontos aplicáveis a um contrato.

    Args:
        plan_id: ID do plano
        payment_method: Método de pagamento
        amount: Valor base
        contract_start_date: Data de início do contrato (para verificar duração do desconto)
    """
    if contract_start_date is None:
        contract_start_date = date.today()

    plan_discount_value = 0.0
    payment_method_discount_value = 0.0

    # Buscar desconto por plano
    plan_discount = db.query(PlanDiscount).filter(
        PlanDiscount.plan_id == plan_id,
        PlanDiscount.is_active == True
    ).first()

    if plan_discount:
        # Verificar se o desconto ainda está válido (baseado na duração)
        if plan_discount.duration_months:
            expiry_date = contract_start_date + relativedelta(months=plan_discount.duration_months)
            if date.today() <= expiry_date:
                plan_discount_value = calculate_discount(
                    amount,
                    plan_discount.discount_type,
                    plan_discount.discount_value
                )
        else:
            # Desconto permanente
            plan_discount_value = calculate_discount(
                amount,
                plan_discount.discount_type,
                plan_discount.discount_value
            )

    # Buscar desconto por forma de pagamento (específico do plano ou global)
    payment_discount = db.query(PaymentMethodDiscount).filter(
        PaymentMethodDiscount.payment_method == payment_method,
        PaymentMethodDiscount.is_active == True
    ).filter(
        (PaymentMethodDiscount.plan_id == plan_id) | (PaymentMethodDiscount.plan_id.is_(None))
    ).order_by(
        PaymentMethodDiscount.plan_id.desc()  # Priorizar desconto específico do plano
    ).first()

    if payment_discount:
        # Aplicar desconto sobre o valor já descontado pelo plano
        amount_after_plan_discount = amount - plan_discount_value
        payment_method_discount_value = calculate_discount(
            amount_after_plan_discount,
            payment_discount.discount_type,
            payment_discount.discount_value
        )

    total_discount = plan_discount_value + payment_method_discount_value
    final_amount = amount - total_discount

    return DiscountCalculation(
        original_amount=amount,
        plan_discount=plan_discount_value if plan_discount_value > 0 else None,
        payment_method_discount=payment_method_discount_value if payment_method_discount_value > 0 else None,
        total_discount=total_discount,
        final_amount=final_amount
    )


def get_active_plan_discounts(db: Session, plan_id: int) -> list[PlanDiscount]:
    """
    Retorna descontos ativos para um plano.
    """
    return db.query(PlanDiscount).filter(
        PlanDiscount.plan_id == plan_id,
        PlanDiscount.is_active == True
    ).all()


def get_active_payment_method_discounts(db: Session, payment_method: str, plan_id: int = None) -> list[PaymentMethodDiscount]:
    """
    Retorna descontos ativos para uma forma de pagamento.
    """
    q = db.query(PaymentMethodDiscount).filter(
        PaymentMethodDiscount.payment_method == payment_method,
        PaymentMethodDiscount.is_active == True
    )

    if plan_id:
        q = q.filter(
            (PaymentMethodDiscount.plan_id == plan_id) | (PaymentMethodDiscount.plan_id.is_(None))
        )

    return q.all()
