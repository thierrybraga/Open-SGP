"""
Arquivo: app/modules/administration/employees/schemas.py

Responsabilidade:
Schemas Pydantic para Employees.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date


class EmployeeCreate(BaseModel):
    full_name: str
    document: str
    rg: Optional[str] = None
    birth_date: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    admission_date: Optional[date] = None
    salary: Optional[float] = None
    payment_type: Optional[str] = None
    bank_code: Optional[str] = None
    bank_agency: Optional[str] = None
    bank_account: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator('document')
    @classmethod
    def validate_document(cls, v):
        # Remover pontuação
        v = v.replace('.', '').replace('-', '').replace('/', '')
        if len(v) != 11:
            raise ValueError('document must be a valid CPF (11 digits)')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['active', 'inactive', 'vacation', 'sick_leave', 'terminated']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v

    @field_validator('payment_type')
    @classmethod
    def validate_payment_type(cls, v):
        if v and v not in ['monthly', 'hourly', 'commission', 'daily']:
            raise ValueError('payment_type must be monthly, hourly, commission or daily')
        return v


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    document: Optional[str] = None
    rg: Optional[str] = None
    birth_date: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    admission_date: Optional[date] = None
    termination_date: Optional[date] = None
    salary: Optional[float] = None
    payment_type: Optional[str] = None
    bank_code: Optional[str] = None
    bank_agency: Optional[str] = None
    bank_account: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    document: str
    rg: Optional[str] = None
    birth_date: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    admission_date: Optional[date] = None
    termination_date: Optional[date] = None
    salary: Optional[float] = None
    payment_type: Optional[str] = None
    bank_code: Optional[str] = None
    bank_agency: Optional[str] = None
    bank_account: Optional[str] = None
    status: str
    is_active: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True
