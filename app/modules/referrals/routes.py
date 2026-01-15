"""
Arquivo: app/modules/referrals/routes.py

Responsabilidade:
Rotas REST para Indicações.

Integrações:
- core.dependencies
- modules.referrals.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Referral, ReferralReward, ReferralProgram
from .schemas import (
    ReferralCreate, ReferralUpdate, ReferralOut,
    ReferralRewardCreate, ReferralRewardUpdate, ReferralRewardOut,
    ReferralProgramCreate, ReferralProgramUpdate, ReferralProgramOut,
    ReferralStats
)
from .service import (
    create_referral, update_referral, convert_referral,
    create_referral_reward, pay_reward, get_referral_stats,
    create_referral_program, update_referral_program
)


router = APIRouter()


# ===== REFERRALS =====

@router.get("/", response_model=List[ReferralOut])
def list_referrals(
    referrer_client_id: Optional[int] = Query(default=None),
    referred_client_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    Lista indicações.
    """
    q = db.query(Referral)

    if referrer_client_id:
        q = q.filter(Referral.referrer_client_id == referrer_client_id)
    if referred_client_id:
        q = q.filter(Referral.referred_client_id == referred_client_id)
    if status_filter:
        q = q.filter(Referral.status == status_filter)

    referrals = q.order_by(Referral.created_at.desc()).all()
    return [ReferralOut(**r.__dict__) for r in referrals]


@router.post("/", response_model=ReferralOut, dependencies=[Depends(require_permissions("referrals.create"))])
def create_referral_endpoint(data: ReferralCreate, db: Session = Depends(get_db)):
    """
    Cria nova indicação.
    """
    try:
        referral = create_referral(db, data)
        return ReferralOut(**referral.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{referral_id}", response_model=ReferralOut)
def get_referral(referral_id: int, db: Session = Depends(get_db)):
    """
    Busca indicação por ID.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    return ReferralOut(**referral.__dict__)


@router.put("/{referral_id}", response_model=ReferralOut, dependencies=[Depends(require_permissions("referrals.update"))])
def update_referral_endpoint(
    referral_id: int,
    data: ReferralUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza indicação.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    referral = update_referral(db, referral, data)
    return ReferralOut(**referral.__dict__)


@router.post("/{referral_id}/convert", response_model=ReferralOut, dependencies=[Depends(require_permissions("referrals.update"))])
def convert_referral_endpoint(
    referral_id: int,
    contract_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    Converte indicação (marca como cliente ativo) e cria recompensas.
    """
    try:
        referral = convert_referral(db, referral_id, contract_id)
        return ReferralOut(**referral.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{referral_id}", dependencies=[Depends(require_permissions("referrals.delete"))])
def delete_referral(referral_id: int, db: Session = Depends(get_db)):
    """
    Remove indicação.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")

    db.delete(referral)
    db.commit()

    return {"message": "Referral deleted successfully"}


# ===== REWARDS =====

@router.get("/rewards/list", response_model=List[ReferralRewardOut])
def list_rewards(
    referral_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    Lista recompensas.
    """
    q = db.query(ReferralReward)

    if referral_id:
        q = q.filter(ReferralReward.referral_id == referral_id)
    if status_filter:
        q = q.filter(ReferralReward.status == status_filter)

    rewards = q.order_by(ReferralReward.created_at.desc()).all()
    return [ReferralRewardOut(**r.__dict__) for r in rewards]


@router.post("/rewards", response_model=ReferralRewardOut, dependencies=[Depends(require_permissions("referrals.rewards.create"))])
def create_reward_endpoint(data: ReferralRewardCreate, db: Session = Depends(get_db)):
    """
    Cria recompensa manual.
    """
    reward = create_referral_reward(db, data)
    return ReferralRewardOut(**reward.__dict__)


@router.post("/rewards/{reward_id}/pay", response_model=ReferralRewardOut, dependencies=[Depends(require_permissions("referrals.rewards.pay"))])
def pay_reward_endpoint(
    reward_id: int,
    payment_reference: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Marca recompensa como paga.
    """
    try:
        reward = pay_reward(db, reward_id, payment_reference)
        return ReferralRewardOut(**reward.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== PROGRAMS =====

@router.get("/programs/list", response_model=List[ReferralProgramOut])
def list_programs(
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista programas de indicações.
    """
    q = db.query(ReferralProgram)

    if is_active is not None:
        q = q.filter(ReferralProgram.is_active == is_active)

    programs = q.order_by(ReferralProgram.created_at.desc()).all()
    return [ReferralProgramOut(**p.__dict__) for p in programs]


@router.post("/programs", response_model=ReferralProgramOut, dependencies=[Depends(require_permissions("referrals.programs.create"))])
def create_program_endpoint(data: ReferralProgramCreate, db: Session = Depends(get_db)):
    """
    Cria programa de indicações.
    """
    program = create_referral_program(db, data)
    return ReferralProgramOut(**program.__dict__)


@router.put("/programs/{program_id}", response_model=ReferralProgramOut, dependencies=[Depends(require_permissions("referrals.programs.update"))])
def update_program_endpoint(
    program_id: int,
    data: ReferralProgramUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza programa de indicações.
    """
    program = db.query(ReferralProgram).filter(ReferralProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    program = update_referral_program(db, program, data)
    return ReferralProgramOut(**program.__dict__)


# ===== STATS =====

@router.get("/stats/summary", response_model=ReferralStats)
def get_referral_statistics(db: Session = Depends(get_db)):
    """
    Retorna estatísticas do programa de indicações.
    """
    return ReferralStats(**get_referral_stats(db))
