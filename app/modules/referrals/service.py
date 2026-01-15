"""
Arquivo: app/modules/referrals/service.py

Responsabilidade:
Lógica de negócio para Indicações.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from .models import Referral, ReferralReward, ReferralProgram
from .schemas import ReferralCreate, ReferralUpdate, ReferralRewardCreate


def create_referral(db: Session, data: ReferralCreate) -> Referral:
    """Cria nova indicação."""
    # Verificar se não está se auto-indicando
    if data.referrer_client_id == data.referred_client_id:
        raise ValueError("Client cannot refer themselves")

    # Verificar se já existe indicação
    existing = db.query(Referral).filter(
        Referral.referrer_client_id == data.referrer_client_id,
        Referral.referred_client_id == data.referred_client_id
    ).first()

    if existing:
        raise ValueError("Referral already exists")

    # Verificar limite de indicações (se houver programa ativo)
    program = db.query(ReferralProgram).filter(
        ReferralProgram.is_active == True
    ).first()

    if program and program.max_referrals_per_client > 0:
        count = db.query(func.count(Referral.id)).filter(
            Referral.referrer_client_id == data.referrer_client_id
        ).scalar()

        if count >= program.max_referrals_per_client:
            raise ValueError(f"Maximum referrals limit reached ({program.max_referrals_per_client})")

    referral = Referral(**data.dict())
    db.add(referral)
    db.commit()
    db.refresh(referral)
    return referral


def update_referral(db: Session, referral: Referral, data: ReferralUpdate) -> Referral:
    """Atualiza indicação."""
    for field, value in data.dict(exclude_none=True).items():
        setattr(referral, field, value)

    db.add(referral)
    db.commit()
    db.refresh(referral)
    return referral


def convert_referral(db: Session, referral_id: int, contract_id: int) -> Referral:
    """
    Marca indicação como convertida e cria recompensa.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise ValueError("Referral not found")

    if referral.status != "pending":
        raise ValueError("Referral is not pending")

    # Atualizar indicação
    referral.status = "converted"
    referral.referred_contract_id = contract_id
    referral.converted_at = datetime.utcnow().isoformat()

    db.add(referral)
    db.flush()

    # Criar recompensa automaticamente
    program = db.query(ReferralProgram).filter(
        ReferralProgram.is_active == True
    ).first()

    if program:
        # Recompensa para quem indicou
        reward = ReferralReward(
            referral_id=referral.id,
            reward_type=program.default_reward_type,
            reward_value=program.default_reward_value,
            currency="BRL",
            status="pending",
            description=f"Recompensa por indicação - Cliente #{referral.referred_client_id}"
        )
        db.add(reward)

        # Recompensa para quem foi indicado (se configurado)
        if program.reward_referred_client and program.referred_reward_value > 0:
            referred_reward = ReferralReward(
                referral_id=referral.id,
                reward_type=program.default_reward_type,
                reward_value=program.referred_reward_value,
                currency="BRL",
                status="pending",
                description=f"Bônus de boas-vindas por indicação"
            )
            db.add(referred_reward)

    db.commit()
    db.refresh(referral)
    return referral


def create_referral_reward(db: Session, data: ReferralRewardCreate) -> ReferralReward:
    """Cria recompensa manual."""
    reward = ReferralReward(**data.dict())
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return reward


def pay_reward(db: Session, reward_id: int, payment_reference: str = None) -> ReferralReward:
    """Marca recompensa como paga."""
    reward = db.query(ReferralReward).filter(ReferralReward.id == reward_id).first()
    if not reward:
        raise ValueError("Reward not found")

    if reward.status == "paid":
        raise ValueError("Reward already paid")

    reward.status = "paid"
    reward.paid_at = datetime.utcnow().isoformat()
    reward.payment_reference = payment_reference

    db.add(reward)

    # Atualizar status da indicação
    referral = reward.referral
    if referral and referral.status == "converted":
        # Verificar se todas as recompensas foram pagas
        pending_rewards = db.query(ReferralReward).filter(
            ReferralReward.referral_id == referral.id,
            ReferralReward.status != "paid"
        ).count()

        if pending_rewards == 0:
            referral.status = "rewarded"
            db.add(referral)

    db.commit()
    db.refresh(reward)
    return reward


def get_referral_stats(db: Session) -> dict:
    """Retorna estatísticas do programa de indicações."""
    total_referrals = db.query(func.count(Referral.id)).scalar()

    pending = db.query(func.count(Referral.id)).filter(
        Referral.status == "pending"
    ).scalar()

    converted = db.query(func.count(Referral.id)).filter(
        Referral.status.in_(["converted", "rewarded"])
    ).scalar()

    total_pending_rewards = db.query(func.sum(ReferralReward.reward_value)).filter(
        ReferralReward.status == "pending"
    ).scalar()

    total_paid_rewards = db.query(func.sum(ReferralReward.reward_value)).filter(
        ReferralReward.status == "paid"
    ).scalar()

    # Top referrers
    top_referrers = db.query(
        Referral.referrer_client_id,
        func.count(Referral.id).label('count')
    ).group_by(
        Referral.referrer_client_id
    ).order_by(
        func.count(Referral.id).desc()
    ).limit(10).all()

    return {
        "total_referrals": total_referrals or 0,
        "pending_referrals": pending or 0,
        "converted_referrals": converted or 0,
        "total_rewards_pending": float(total_pending_rewards) if total_pending_rewards else 0.0,
        "total_rewards_paid": float(total_paid_rewards) if total_paid_rewards else 0.0,
        "top_referrers": [
            {"client_id": r.referrer_client_id, "count": r.count}
            for r in top_referrers
        ]
    }


def create_referral_program(db: Session, data) -> ReferralProgram:
    """Cria programa de indicações."""
    program = ReferralProgram(**data.dict())
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


def update_referral_program(db: Session, program: ReferralProgram, data) -> ReferralProgram:
    """Atualiza programa de indicações."""
    for field, value in data.dict(exclude_none=True).items():
        setattr(program, field, value)

    db.add(program)
    db.commit()
    db.refresh(program)
    return program
