"""
Arquivo: app/modules/referrals/schemas.py

Responsabilidade:
Schemas Pydantic para Indicações.
"""

from pydantic import BaseModel, field_validator
from typing import Optional


class ReferralCreate(BaseModel):
    referrer_client_id: int
    referred_client_id: int
    referral_code: Optional[str] = None
    notes: Optional[str] = None


class ReferralUpdate(BaseModel):
    status: Optional[str] = None
    referred_contract_id: Optional[int] = None
    converted_at: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in ['pending', 'converted', 'rewarded', 'cancelled']:
            raise ValueError('Invalid status')
        return v


class ReferralOut(BaseModel):
    id: int
    referrer_client_id: int
    referred_client_id: int
    referred_contract_id: Optional[int] = None
    status: str
    converted_at: Optional[str] = None
    referral_code: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ReferralRewardCreate(BaseModel):
    referral_id: int
    reward_type: str  # discount, cash, credit, bonus
    reward_value: float
    currency: str = "BRL"
    description: Optional[str] = None

    @field_validator('reward_type')
    @classmethod
    def validate_reward_type(cls, v):
        if v not in ['discount', 'cash', 'credit', 'bonus']:
            raise ValueError('Invalid reward type')
        return v


class ReferralRewardUpdate(BaseModel):
    status: Optional[str] = None
    paid_at: Optional[str] = None
    payment_reference: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in ['pending', 'approved', 'paid', 'cancelled']:
            raise ValueError('Invalid status')
        return v


class ReferralRewardOut(BaseModel):
    id: int
    referral_id: int
    reward_type: str
    reward_value: float
    currency: str
    status: str
    paid_at: Optional[str] = None
    payment_reference: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class ReferralProgramCreate(BaseModel):
    name: str
    description: Optional[str] = None
    default_reward_type: str = "discount"
    default_reward_value: float = 0.0
    reward_referred_client: bool = False
    referred_reward_value: float = 0.0
    min_active_months: int = 1
    max_referrals_per_client: int = 0
    is_active: bool = True
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None


class ReferralProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_reward_type: Optional[str] = None
    default_reward_value: Optional[float] = None
    reward_referred_client: Optional[bool] = None
    referred_reward_value: Optional[float] = None
    min_active_months: Optional[int] = None
    max_referrals_per_client: Optional[int] = None
    is_active: Optional[bool] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None


class ReferralProgramOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    default_reward_type: str
    default_reward_value: float
    reward_referred_client: bool
    referred_reward_value: float
    min_active_months: int
    max_referrals_per_client: int
    is_active: bool
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None

    class Config:
        from_attributes = True


class ReferralStats(BaseModel):
    """Estatísticas do programa de indicações."""
    total_referrals: int
    pending_referrals: int
    converted_referrals: int
    total_rewards_pending: float
    total_rewards_paid: float
    top_referrers: list
