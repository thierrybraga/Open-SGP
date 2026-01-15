"""
Arquivo: app/modules/discounts/schemas.py

Responsabilidade:
Schemas Pydantic para Descontos.
"""

from pydantic import BaseModel, field_validator
from typing import Optional


# ===== PLAN DISCOUNTS =====

class PlanDiscountCreate(BaseModel):
    plan_id: int
    name: str
    description: Optional[str] = None
    discount_type: str  # percentage, fixed
    discount_value: float
    duration_months: Optional[int] = None
    is_active: bool = True

    @field_validator('discount_type')
    @classmethod
    def validate_discount_type(cls, v):
        if v not in ['percentage', 'fixed']:
            raise ValueError('discount_type must be percentage or fixed')
        return v

    @field_validator('discount_value')
    @classmethod
    def validate_discount_value(cls, v):
        if v < 0:
            raise ValueError('discount_value must be positive')
        return v

    @field_validator('duration_months')
    @classmethod
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError('duration_months must be positive')
        return v


class PlanDiscountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    duration_months: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator('discount_type')
    @classmethod
    def validate_discount_type(cls, v):
        if v is not None and v not in ['percentage', 'fixed']:
            raise ValueError('discount_type must be percentage or fixed')
        return v

    @field_validator('discount_value')
    @classmethod
    def validate_discount_value(cls, v):
        if v is not None and v < 0:
            raise ValueError('discount_value must be positive')
        return v


class PlanDiscountOut(BaseModel):
    id: int
    plan_id: int
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    duration_months: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


# ===== PAYMENT METHOD DISCOUNTS =====

class PaymentMethodDiscountCreate(BaseModel):
    name: str
    description: Optional[str] = None
    payment_method: str  # automatic_debit, credit_card, pix, boleto
    discount_type: str  # percentage, fixed
    discount_value: float
    plan_id: Optional[int] = None
    is_active: bool = True

    @field_validator('discount_type')
    @classmethod
    def validate_discount_type(cls, v):
        if v not in ['percentage', 'fixed']:
            raise ValueError('discount_type must be percentage or fixed')
        return v

    @field_validator('discount_value')
    @classmethod
    def validate_discount_value(cls, v):
        if v < 0:
            raise ValueError('discount_value must be positive')
        return v


class PaymentMethodDiscountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    plan_id: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator('discount_type')
    @classmethod
    def validate_discount_type(cls, v):
        if v is not None and v not in ['percentage', 'fixed']:
            raise ValueError('discount_type must be percentage or fixed')
        return v

    @field_validator('discount_value')
    @classmethod
    def validate_discount_value(cls, v):
        if v is not None and v < 0:
            raise ValueError('discount_value must be positive')
        return v


class PaymentMethodDiscountOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    payment_method: str
    discount_type: str
    discount_value: float
    plan_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


# ===== CALCULATION =====

class DiscountCalculation(BaseModel):
    original_amount: float
    plan_discount: Optional[float] = None
    payment_method_discount: Optional[float] = None
    total_discount: float
    final_amount: float
