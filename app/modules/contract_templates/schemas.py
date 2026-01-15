"""
Arquivo: app/modules/contract_templates/schemas.py

Responsabilidade:
Esquemas Pydantic para Templates de Contrato e Aditivos.

Integrações:
- modules.contract_templates.models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ContractTemplateCreate(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    content: str
    available_variables: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class ContractTemplateUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    available_variables: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ContractTemplateOut(BaseModel):
    id: int
    name: str
    version: str
    description: Optional[str]
    content: str
    available_variables: Optional[str]
    is_active: bool
    is_default: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractAddendumCreate(BaseModel):
    contract_id: int
    type: str
    title: str
    description: str
    effective_date: datetime
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    document_url: Optional[str] = None


class ContractAddendumUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    effective_date: Optional[datetime] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    document_url: Optional[str] = None


class ContractAddendumOut(BaseModel):
    id: int
    contract_id: int
    addendum_number: int
    type: str
    title: str
    description: str
    effective_date: datetime
    old_value: Optional[str]
    new_value: Optional[str]
    document_url: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateContractRequest(BaseModel):
    template_id: int
    contract_id: int
    variables: Optional[dict] = {}


class GenerateContractOut(BaseModel):
    contract_html: str
    contract_pdf_url: Optional[str] = None
