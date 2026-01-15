"""
Arquivo: app/modules/cashier/routes.py

Responsabilidade:
Rotas REST para Caixa.

Integrações:
- core.dependencies
- modules.cashier.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date

from ...core.dependencies import get_db, require_permissions, get_current_user
from .models import CashRegister, CashMovement
from .schemas import (
    CashRegisterOpen,
    CashRegisterClose,
    CashRegisterOut,
    CashMovementCreate,
    CashMovementOut,
    CashRegisterSummary,
    CashRegisterReport
)
from .service import (
    open_cash_register,
    close_cash_register,
    create_movement,
    get_cash_register_summary
)


router = APIRouter()


# ===== CAIXA =====

@router.post("/open", response_model=CashRegisterOut, dependencies=[Depends(require_permissions("cashier.open"))])
def open_cash_endpoint(
    data: CashRegisterOpen,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Abre um novo caixa para o usuário atual.
    """
    try:
        cash_register = open_cash_register(db, data, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CashRegisterOut(**cash_register.__dict__)


@router.post("/{cash_register_id}/close", response_model=CashRegisterOut, dependencies=[Depends(require_permissions("cashier.close"))])
def close_cash_endpoint(
    cash_register_id: int,
    data: CashRegisterClose,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Fecha um caixa.
    """
    cash_register = db.query(CashRegister).filter(CashRegister.id == cash_register_id).first()
    if not cash_register:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash register not found")

    # Verificar se é o dono do caixa
    if cash_register.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to close this cash register")

    try:
        cash_register = close_cash_register(db, cash_register, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CashRegisterOut(**cash_register.__dict__)


@router.get("/", response_model=List[CashRegisterOut])
def list_cash_registers(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    user_id: Optional[int] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista registros de caixa.
    """
    q = db.query(CashRegister)

    if status_filter:
        q = q.filter(CashRegister.status == status_filter)
    if user_id:
        q = q.filter(CashRegister.user_id == user_id)
    if date_from:
        q = q.filter(CashRegister.opened_at >= date_from)
    if date_to:
        q = q.filter(CashRegister.opened_at <= date_to)

    items = q.order_by(CashRegister.opened_at.desc()).all()
    return [CashRegisterOut(**c.__dict__) for c in items]


@router.get("/current", response_model=CashRegisterOut)
def get_current_cash_register(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retorna o caixa aberto do usuário atual.
    """
    cash_register = db.query(CashRegister).filter(
        CashRegister.user_id == current_user.id,
        CashRegister.status == "open"
    ).first()

    if not cash_register:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No open cash register found")

    return CashRegisterOut(**cash_register.__dict__)


@router.get("/{cash_register_id}", response_model=CashRegisterOut)
def get_cash_register(cash_register_id: int, db: Session = Depends(get_db)):
    """
    Busca registro de caixa por ID.
    """
    cash_register = db.query(CashRegister).filter(CashRegister.id == cash_register_id).first()
    if not cash_register:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash register not found")

    return CashRegisterOut(**cash_register.__dict__)


@router.get("/{cash_register_id}/summary", response_model=CashRegisterSummary)
def get_summary(cash_register_id: int, db: Session = Depends(get_db)):
    """
    Retorna resumo de um caixa.
    """
    summary = get_cash_register_summary(db, cash_register_id)
    return summary


@router.get("/{cash_register_id}/report", response_model=CashRegisterReport)
def get_report(cash_register_id: int, db: Session = Depends(get_db)):
    """
    Retorna relatório completo de um caixa.
    """
    cash_register = db.query(CashRegister).filter(CashRegister.id == cash_register_id).first()
    if not cash_register:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash register not found")

    summary = get_cash_register_summary(db, cash_register_id)
    movements = db.query(CashMovement).filter(CashMovement.cash_register_id == cash_register_id).all()

    return CashRegisterReport(
        cash_register=CashRegisterOut(**cash_register.__dict__),
        summary=summary,
        movements=[CashMovementOut(**m.__dict__) for m in movements]
    )


# ===== MOVIMENTAÇÕES =====

@router.post("/movements", response_model=CashMovementOut, dependencies=[Depends(require_permissions("cashier.movements.create"))])
def create_movement_endpoint(
    data: CashMovementCreate,
    db: Session = Depends(get_db)
):
    """
    Registra uma movimentação no caixa.
    """
    try:
        movement = create_movement(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CashMovementOut(**movement.__dict__)


@router.get("/movements", response_model=List[CashMovementOut])
def list_movements(
    cash_register_id: Optional[int] = Query(default=None),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista movimentações de caixa.
    """
    q = db.query(CashMovement)

    if cash_register_id:
        q = q.filter(CashMovement.cash_register_id == cash_register_id)
    if type_filter:
        q = q.filter(CashMovement.type == type_filter)
    if category:
        q = q.filter(CashMovement.category == category)

    items = q.order_by(CashMovement.created_at.desc()).all()
    return [CashMovementOut(**m.__dict__) for m in items]
