"""
Arquivo: app/modules/reports/service.py

Responsabilidade:
Regras de negócio para Relatórios/Dashboards: CRUD de definições e widgets,
execução de relatórios agregados e cálculo de visão geral.

Integrações:
- modules.reports.models
- modules.clients.models
- modules.contracts.models
- modules.billing.models
"""

from time import perf_counter
from sqlalchemy.orm import Session

from .models import ReportDefinition, DashboardWidget, ReportExecutionLog
from .schemas import (
    ReportDefinitionCreate,
    ReportDefinitionUpdate,
    ReportRunRequest,
    ReportRunResult,
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
    DashboardOverview,
)

from ..clients.models import Client
from ..contracts.models import Contract
from ..billing.models import Title
from ..service_orders.models import ServiceOrder
from ..network.models import ContractNetworkAssignment
from ..communication.models import MessageQueue
from datetime import datetime, timedelta


def create_report_definition(db: Session, data: ReportDefinitionCreate) -> ReportDefinition:
    r = ReportDefinition(**data.dict())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def update_report_definition(db: Session, r: ReportDefinition, data: ReportDefinitionUpdate) -> ReportDefinition:
    for field, value in data.dict(exclude_none=True).items():
        setattr(r, field, value)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def delete_report_definition(db: Session, r: ReportDefinition) -> None:
    db.delete(r)
    db.commit()


def run_report(db: Session, r: ReportDefinition, req: ReportRunRequest) -> ReportRunResult:
    start = perf_counter()
    data = []
    status = "success"
    error = None
    try:
        if r.query_type == "aggregate":
            if r.code == "financial_overview":
                overdue_titles = db.query(Title).filter(Title.status == "overdue").all()
                amount_overdue = sum(t.amount for t in overdue_titles)
                data = [
                    {
                        "titles_overdue": len(overdue_titles),
                        "amount_overdue": float(amount_overdue),
                    }
                ]
            elif r.code == "clients_overview":
                clients_total = db.query(Client).count()
                clients_active = db.query(Client).filter(Client.is_active == True).count()
                data = [
                    {
                        "clients_total": clients_total,
                        "clients_active": clients_active,
                    }
                ]
            elif r.code == "anatel_sici":
                clients_total = db.query(Client).count()
                contracts_active = db.query(Contract).filter(Contract.status == "active").count()
                data = [
                    {
                        "anatel_sici_version": "2025.1",
                        "clients_total": clients_total,
                        "contracts_active": contracts_active,
                    }
                ]
            elif r.code == "anatel_ppp_scm":
                contracts_active = db.query(Contract).filter(Contract.status == "active").count()
                titles_overdue = db.query(Title).filter(Title.status == "overdue").count()
                data = [
                    {
                        "ppp_scm_version": "2025.1",
                        "contracts_active": contracts_active,
                        "titles_overdue": titles_overdue,
                    }
                ]
            else:
                data = []
        else:
            status = "failed"
            error = "Unsupported query_type"
    except Exception as e:
        status = "failed"
        error = str(e)

    duration_ms = int((perf_counter() - start) * 1000)
    rows_count = len(data)

    log = ReportExecutionLog(
        report_id=r.id,
        duration_ms=duration_ms,
        status=status,
        error=error,
        rows_count=rows_count,
    )
    db.add(log)
    db.commit()

    return ReportRunResult(status=status, rows_count=rows_count, duration_ms=duration_ms, data=data)


def create_widget(db: Session, data: DashboardWidgetCreate) -> DashboardWidget:
    w = DashboardWidget(**data.dict())
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def update_widget(db: Session, w: DashboardWidget, data: DashboardWidgetUpdate) -> DashboardWidget:
    for field, value in data.dict(exclude_none=True).items():
        setattr(w, field, value)
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def dashboard_overview(db: Session) -> DashboardOverview:
    clients_total = db.query(Client).count()
    clients_active = db.query(Client).filter(Client.is_active == True).count()
    contracts_active = db.query(Contract).filter(Contract.status == "active").count()
    overdue_titles_q = db.query(Title).filter(Title.status == "overdue")
    titles_overdue = overdue_titles_q.count()
    amount_overdue = sum(t.amount for t in overdue_titles_q.all())
    blocked_contracts = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.status == "blocked").count()
    service_orders_in_progress = db.query(ServiceOrder).filter(ServiceOrder.status == "in_progress").count()
    last_msgs = db.query(MessageQueue).order_by(MessageQueue.created_at.desc()).limit(100).all()
    sent = len([m for m in last_msgs if m.status == "sent"]) if last_msgs else 0
    rate = (sent / len(last_msgs) * 100.0) if last_msgs else 0.0

    return DashboardOverview(
        clients_total=clients_total,
        clients_active=clients_active,
        contracts_active=contracts_active,
        titles_overdue=titles_overdue,
        amount_overdue=float(amount_overdue),
        blocked_contracts=blocked_contracts,
        service_orders_in_progress=service_orders_in_progress,
        communication_success_rate=rate,
    )


def timeseries_communication_success(db: Session, days: int = 7) -> list[dict]:
    base = datetime.utcnow().date()
    out: list[dict] = []
    for i in range(days):
        day = base - timedelta(days=days - 1 - i)
        msgs = db.query(MessageQueue).filter(
            MessageQueue.created_at >= datetime.combine(day, datetime.min.time()),
            MessageQueue.created_at < datetime.combine(day + timedelta(days=1), datetime.min.time()),
        ).all()
        total = len(msgs)
        sent = len([m for m in msgs if m.status == "sent"]) if total else 0
        rate = (sent / total * 100.0) if total else 0.0
        out.append({"date": day.isoformat(), "success_rate": rate})
    return out


def timeseries_service_orders_status(db: Session, days: int = 7) -> list[dict]:
    base = datetime.utcnow().date()
    statuses = ["open", "scheduled", "in_progress", "completed", "canceled"]
    out: list[dict] = []
    for i in range(days):
        day = base - timedelta(days=days - 1 - i)
        q = db.query(ServiceOrder).filter(
            ServiceOrder.created_at >= datetime.combine(day, datetime.min.time()),
            ServiceOrder.created_at < datetime.combine(day + timedelta(days=1), datetime.min.time()),
        )
        counts = {s: 0 for s in statuses}
        for o in q.all():
            counts[o.status] = counts.get(o.status, 0) + 1
        out.append({"date": day.isoformat(), **counts})
    return out


def communication_success_by_provider(db: Session, days: int = 7) -> list[dict]:
    base = datetime.utcnow().date()
    start = datetime.combine(base - timedelta(days=days), datetime.min.time())
    msgs = db.query(MessageQueue).filter(MessageQueue.created_at >= start).all()
    by_provider: dict[str, dict] = {}
    for m in msgs:
        prov = (m.provider or "-").lower()
        p = by_provider.setdefault(prov, {"total": 0, "sent": 0})
        p["total"] += 1
        if m.status == "sent":
            p["sent"] += 1
    out: list[dict] = []
    for prov, v in by_provider.items():
        rate = (v["sent"] / v["total"] * 100.0) if v["total"] else 0.0
        out.append({"provider": prov, "total": v["total"], "sent": v["sent"], "success_rate": rate})
    out.sort(key=lambda x: x["provider"]) 
    return out


def sample_onu_metrics(db: Session, limit: int = 10) -> dict:
    from ..network.models import ContractNetworkAssignment, NetworkDevice
    from ..network.service import get_onu_status
    q = (
        db.query(ContractNetworkAssignment)
        .join(NetworkDevice, ContractNetworkAssignment.device_id == NetworkDevice.id)
        .filter(ContractNetworkAssignment.status == "active")
        .filter(NetworkDevice.vendor.in_(["huawei", "zte"]))
        .order_by(ContractNetworkAssignment.updated_at.desc())
        .limit(limit)
    )
    items = []
    rx_vals: list[float] = []
    tx_vals: list[float] = []
    uptimes: list[int] = []
    for a in q.all():
        try:
            status = get_onu_status(db, a.device_id, str(a.contract_id))
            items.append({"contract_id": a.contract_id, **status})
            rv = status.get("rx_power_dbm")
            tv = status.get("tx_power_dbm")
            up = status.get("uptime_seconds")
            if isinstance(rv, (int, float)):
                rx_vals.append(float(rv))
            if isinstance(tv, (int, float)):
                tx_vals.append(float(tv))
            if isinstance(up, int):
                uptimes.append(up)
        except Exception:
            continue
    def _avg(lst: list[float]) -> float:
        return (sum(lst) / len(lst)) if lst else 0.0
    summary = {
        "count": len(items),
        "avg_rx_power_dbm": _avg(rx_vals),
        "avg_tx_power_dbm": _avg(tx_vals),
        "avg_uptime_seconds": int(_avg(uptimes)) if uptimes else 0,
        "min_rx_power_dbm": min(rx_vals) if rx_vals else None,
        "max_rx_power_dbm": max(rx_vals) if rx_vals else None,
        "items": items,
    }
    return summary


def occurrences_summary(db: Session, days: int = 30) -> dict:
    from ..support.models import Occurrence, Ticket
    from datetime import datetime, timedelta
    start = datetime.utcnow() - timedelta(days=days)
    q = db.query(Occurrence).filter(Occurrence.created_at >= start)
    items = q.all()
    by_category: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    total_open = 0
    total_closed = 0
    for o in items:
        by_category[o.category] = by_category.get(o.category, 0) + 1
        by_severity[o.severity] = by_severity.get(o.severity, 0) + 1
        if o.status == "open":
            total_open += 1
        elif o.status == "closed":
            total_closed += 1
    open_tickets = db.query(Ticket).filter(Ticket.status.in_(["open", "in_progress"]))
    tickets_total = open_tickets.count()
    now = datetime.utcnow()
    sla_overdue = open_tickets.filter(Ticket.sla_due_at.isnot(None)).filter(Ticket.sla_due_at < now).count()
    sla_rate = (sla_overdue / tickets_total * 100.0) if tickets_total else 0.0
    return {
        "total": len(items),
        "total_open": total_open,
        "total_closed": total_closed,
        "by_category": by_category,
        "by_severity": by_severity,
        "tickets_open": tickets_total,
        "tickets_sla_overdue": sla_overdue,
        "tickets_sla_overdue_rate": sla_rate,
    }
