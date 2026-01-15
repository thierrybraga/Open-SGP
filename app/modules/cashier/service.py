"""
Arquivo: app/modules/cashier/service.py

Responsabilidade:
Regras de negócio para Caixa.

Integrações:
- modules.cashier.models
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import CashRegister, CashMovement
from .schemas import (
    CashRegisterOpen,
    CashRegisterClose,
    CashMovementCreate,
    CashRegisterSummary
)


def open_cash_register(db: Session, data: CashRegisterOpen, user_id: int) -> CashRegister:
    """
    Abre um novo caixa.
    """
    # Verificar se já existe caixa aberto para o usuário
    existing = db.query(CashRegister).filter(
        CashRegister.user_id == user_id,
        CashRegister.status == "open"
    ).first()

    if existing:
        raise ValueError("User already has an open cash register")

    # Criar novo registro de caixa
    cash_register = CashRegister(
        user_id=user_id,
        opened_at=datetime.utcnow(),
        opening_balance=data.opening_balance,
        opening_notes=data.opening_notes,
        status="open"
    )

    db.add(cash_register)
    db.commit()
    db.refresh(cash_register)

    return cash_register


def close_cash_register(db: Session, cash_register: CashRegister, data: CashRegisterClose) -> CashRegister:
    """
    Fecha um caixa.
    """
    if cash_register.status != "open":
        raise ValueError("Cash register is not open")

    # Calcular saldo esperado
    expected = calculate_expected_balance(db, cash_register.id)

    # Fechar caixa
    cash_register.closed_at = datetime.utcnow()
    cash_register.closing_balance = data.closing_balance
    cash_register.expected_balance = expected
    cash_register.difference = data.closing_balance - expected
    cash_register.closing_notes = data.closing_notes
    cash_register.status = "closed"

    db.add(cash_register)
    db.commit()
    db.refresh(cash_register)

    return cash_register


def calculate_expected_balance(db: Session, cash_register_id: int) -> float:
    """
    Calcula o saldo esperado do caixa baseado nas movimentações.
    """
    cash_register = db.query(CashRegister).filter(CashRegister.id == cash_register_id).first()
    if not cash_register:
        raise ValueError("Cash register not found")

    # Somar entradas
    total_in = db.query(func.sum(CashMovement.amount)).filter(
        CashMovement.cash_register_id == cash_register_id,
        CashMovement.type == "in"
    ).scalar() or 0.0

    # Somar saídas
    total_out = db.query(func.sum(CashMovement.amount)).filter(
        CashMovement.cash_register_id == cash_register_id,
        CashMovement.type == "out"
    ).scalar() or 0.0

    return cash_register.opening_balance + total_in - total_out


def create_movement(db: Session, data: CashMovementCreate) -> CashMovement:
    """
    Registra uma movimentação no caixa.
    """
    # Verificar se o caixa está aberto
    cash_register = db.query(CashRegister).filter(CashRegister.id == data.cash_register_id).first()
    if not cash_register:
        raise ValueError("Cash register not found")

    if cash_register.status != "open":
        raise ValueError("Cash register is not open")

    # Criar movimentação
    movement = CashMovement(**data.dict())
    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


def get_cash_register_summary(db: Session, cash_register_id: int) -> CashRegisterSummary:
    """
    Gera resumo de um caixa.
    """
    # Totais
    total_in = db.query(func.sum(CashMovement.amount)).filter(
        CashMovement.cash_register_id == cash_register_id,
        CashMovement.type == "in"
    ).scalar() or 0.0

    total_out = db.query(func.sum(CashMovement.amount)).filter(
        CashMovement.cash_register_id == cash_register_id,
        CashMovement.type == "out"
    ).scalar() or 0.0

    # Contagem
    movements_count = db.query(func.count(CashMovement.id)).filter(
        CashMovement.cash_register_id == cash_register_id
    ).scalar() or 0

    # Por categoria
    movements_by_category = {}
    category_data = db.query(
        CashMovement.category,
        func.sum(CashMovement.amount)
    ).filter(
        CashMovement.cash_register_id == cash_register_id
    ).group_by(CashMovement.category).all()

    for category, total in category_data:
        movements_by_category[category] = float(total)

    # Por forma de pagamento
    movements_by_payment_method = {}
    payment_data = db.query(
        CashMovement.payment_method,
        func.sum(CashMovement.amount)
    ).filter(
        CashMovement.cash_register_id == cash_register_id,
        CashMovement.payment_method.isnot(None)
    ).group_by(CashMovement.payment_method).all()

    for method, total in payment_data:
        movements_by_payment_method[method] = float(total)

    return CashRegisterSummary(
        cash_register_id=cash_register_id,
        total_in=total_in,
        total_out=total_out,
        net_balance=total_in - total_out,
        movements_count=movements_count,
        movements_by_category=movements_by_category,
        movements_by_payment_method=movements_by_payment_method
    )
