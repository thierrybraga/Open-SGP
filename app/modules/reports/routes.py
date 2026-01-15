"""
Arquivo: app/modules/reports/routes.py

Responsabilidade:
Rotas REST para Relatórios/Dashboards: CRUD de definições e widgets, execução de
relatórios e visão geral do dashboard.

Integrações:
- core.dependencies
- modules.reports.service
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import ReportDefinition, DashboardWidget
from .schemas import (
    ReportDefinitionCreate,
    ReportDefinitionUpdate,
    ReportDefinitionOut,
    ReportRunRequest,
    ReportRunResult,
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
    DashboardWidgetOut,
    DashboardOverview,
)
from .service import (
    create_report_definition,
    update_report_definition,
    delete_report_definition,
    run_report,
    create_widget,
    update_widget,
    dashboard_overview,
    timeseries_communication_success,
    timeseries_service_orders_status,
    occurrences_summary,
)


router = APIRouter()


@router.get("/definitions", response_model=List[ReportDefinitionOut], dependencies=[Depends(require_permissions("reports.definitions.read"))])
def list_definitions(db: Session = Depends(get_db)):
    items = db.query(ReportDefinition).all()
    return [ReportDefinitionOut(**i.__dict__) for i in items]


@router.post("/definitions", response_model=ReportDefinitionOut, dependencies=[Depends(require_permissions("reports.definitions.create"))])
def create_definition(data: ReportDefinitionCreate, db: Session = Depends(get_db)):
    r = create_report_definition(db, data)
    return ReportDefinitionOut(**r.__dict__)


@router.put("/definitions/{definition_id}", response_model=ReportDefinitionOut, dependencies=[Depends(require_permissions("reports.definitions.update"))])
def update_definition(definition_id: int, data: ReportDefinitionUpdate, db: Session = Depends(get_db)):
    r = db.query(ReportDefinition).filter(ReportDefinition.id == definition_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Definition not found")
    r = update_report_definition(db, r, data)
    return ReportDefinitionOut(**r.__dict__)


@router.delete("/definitions/{definition_id}", dependencies=[Depends(require_permissions("reports.definitions.delete"))])
def delete_definition(definition_id: int, db: Session = Depends(get_db)):
    r = db.query(ReportDefinition).filter(ReportDefinition.id == definition_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Definition not found")
    delete_report_definition(db, r)
    return {"message": "deleted"}


@router.post("/definitions/{definition_id}/run", response_model=ReportRunResult, dependencies=[Depends(require_permissions("reports.run"))])
def run_definition(definition_id: int, req: ReportRunRequest, db: Session = Depends(get_db)):
    r = db.query(ReportDefinition).filter(ReportDefinition.id == definition_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Definition not found")
    return run_report(db, r, req)


@router.get("/widgets", response_model=List[DashboardWidgetOut], dependencies=[Depends(require_permissions("dashboard.widgets.read"))])
def list_widgets(db: Session = Depends(get_db)):
    items = db.query(DashboardWidget).all()
    return [DashboardWidgetOut(**w.__dict__) for w in items]


@router.post("/widgets", response_model=DashboardWidgetOut, dependencies=[Depends(require_permissions("dashboard.widgets.create"))])
def create_widget_endpoint(data: DashboardWidgetCreate, db: Session = Depends(get_db)):
    w = create_widget(db, data)
    return DashboardWidgetOut(**w.__dict__)


@router.put("/widgets/{widget_id}", response_model=DashboardWidgetOut, dependencies=[Depends(require_permissions("dashboard.widgets.update"))])
def update_widget_endpoint(widget_id: int, data: DashboardWidgetUpdate, db: Session = Depends(get_db)):
    w = db.query(DashboardWidget).filter(DashboardWidget.id == widget_id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")
    w = update_widget(db, w, data)
    return DashboardWidgetOut(**w.__dict__)


@router.get("/overview", response_model=DashboardOverview, dependencies=[Depends(require_permissions("dashboard.overview.read"))])
def overview_endpoint(db: Session = Depends(get_db)):
    return dashboard_overview(db)


@router.get("/timeseries/communication-success")
def timeseries_comm_success_endpoint(db: Session = Depends(get_db)):
    return timeseries_communication_success(db)


@router.get("/timeseries/service-orders-status")
def timeseries_os_status_endpoint(db: Session = Depends(get_db)):
    return timeseries_service_orders_status(db)


@router.get("/occurrences/summary")
def occurrences_summary_endpoint(db: Session = Depends(get_db)):
    return occurrences_summary(db)
