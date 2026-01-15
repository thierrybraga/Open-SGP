"""
Arquivo: app/modules/reports/schemas.py

Responsabilidade:
Esquemas Pydantic para Relatórios e Dashboards, incluindo execução e visão geral.

Integrações:
- modules.reports.models
"""

from typing import Optional, Any, List, Dict
from pydantic import BaseModel


class ReportDefinitionCreate(BaseModel):
    name: str
    code: str
    query_type: str
    parameters: Optional[Dict[str, Any]] = None
    is_active: bool = True


class ReportDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    query_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ReportDefinitionOut(BaseModel):
    id: int
    name: str
    code: str
    query_type: str
    parameters: Optional[Dict[str, Any]]
    is_active: bool

    class Config:
        from_attributes = True


class ReportRunRequest(BaseModel):
    parameters: Optional[Dict[str, Any]] = None


class ReportRunResult(BaseModel):
    status: str
    rows_count: int
    duration_ms: int
    data: List[Dict[str, Any]]


class DashboardWidgetCreate(BaseModel):
    name: str
    code: str
    type: str
    config: Optional[Dict[str, Any]] = None
    position_row: int = 0
    position_col: int = 0
    size_x: int = 1
    size_y: int = 1
    is_active: bool = True


class DashboardWidgetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    position_row: Optional[int] = None
    position_col: Optional[int] = None
    size_x: Optional[int] = None
    size_y: Optional[int] = None
    is_active: Optional[bool] = None


class DashboardWidgetOut(BaseModel):
    id: int
    name: str
    code: str
    type: str
    config: Optional[Dict[str, Any]]
    position_row: int
    position_col: int
    size_x: int
    size_y: int
    is_active: bool

    class Config:
        from_attributes = True


class DashboardOverview(BaseModel):
    clients_total: int
    clients_active: int
    contracts_active: int
    titles_overdue: int
    amount_overdue: float
    blocked_contracts: int
    service_orders_in_progress: int
    communication_success_rate: float


class CommunicationSuccessPoint(BaseModel):
    date: str
    success_rate: float


class ServiceOrdersStatusPoint(BaseModel):
    date: str
    open: int
    scheduled: int
    in_progress: int
    completed: int
    canceled: int
