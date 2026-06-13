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
from sqlalchemy import func
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
from ..billing.models import Payment, Remittance, ReturnFile, Title
from ..service_orders.models import ServiceOrder
from ..network.models import ContractNetworkAssignment
from ..communication.models import MessageQueue
from datetime import date, datetime, timedelta
from decimal import Decimal
from ipaddress import ip_network


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


def analytics_overview(db: Session, months: int = 6) -> dict:
    from ..billing.gateway.models import PaymentCharge
    from ..clients.models import Client
    from ..contracts.models import Contract
    from ..fiscal.models import Invoice, ServicePlanDetail
    from ..network.models import IPLease, IPPool, NetworkDevice, RadAcct
    from ..plans.models import Plan
    from ..service_orders.models import ServiceOrder
    from ..stock.models import Comodato, StockItem, StockMovement, Warehouse
    from ..support.models import Ticket, TicketCategory, TicketMessage

    today = date.today()
    now = datetime.utcnow()
    month_starts = _month_starts(today, months)
    current_month_start = month_starts[-1]
    next_month = _next_month(current_month_start)

    active_contracts = (
        db.query(Contract)
        .outerjoin(Plan, Contract.plan_id == Plan.id)
        .filter(Contract.status == "active")
        .all()
    )
    mrr = sum(_contract_price(c) for c in active_contracts)
    arr = mrr * 12

    paid_titles = db.query(Title).filter(Title.status == "paid", Title.paid_date.isnot(None)).all()
    dso_values = [(t.paid_date - t.issue_date).days for t in paid_titles if t.paid_date and t.issue_date]
    dso = round(sum(dso_values) / len(dso_values), 1) if dso_values else 0.0

    open_overdue = db.query(Title).filter(Title.status.in_(["open", "overdue"]), Title.due_date < today).all()
    aging = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    for title in open_overdue:
        days = (today - title.due_date).days
        bucket = "0-30" if days <= 30 else "31-60" if days <= 60 else "61-90" if days <= 90 else "90+"
        aging[bucket] += float(title.amount or 0)

    revenue_monthly = []
    activations_monthly = []
    cancellations_monthly = []
    for start in month_starts:
        end = _next_month(start)
        revenue = (
            db.query(func.sum(Payment.amount))
            .filter(Payment.payment_date >= start, Payment.payment_date < end)
            .scalar()
            or Decimal("0")
        )
        activations = (
            db.query(func.count(Contract.id))
            .filter(Contract.created_at >= datetime.combine(start, datetime.min.time()))
            .filter(Contract.created_at < datetime.combine(end, datetime.min.time()))
            .scalar()
            or 0
        )
        cancellations = (
            db.query(func.count(Contract.id))
            .filter(Contract.status == "canceled")
            .filter(Contract.updated_at >= datetime.combine(start, datetime.min.time()))
            .filter(Contract.updated_at < datetime.combine(end, datetime.min.time()))
            .scalar()
            or 0
        )
        revenue_monthly.append({"label": start.strftime("%m/%Y"), "value": float(revenue)})
        activations_monthly.append({"label": start.strftime("%m/%Y"), "value": activations})
        cancellations_monthly.append({"label": start.strftime("%m/%Y"), "value": cancellations})

    canceled_month_value = 0.0
    canceled_contracts = (
        db.query(Contract)
        .filter(Contract.status == "canceled")
        .filter(Contract.updated_at >= datetime.combine(current_month_start, datetime.min.time()))
        .filter(Contract.updated_at < datetime.combine(next_month, datetime.min.time()))
        .all()
    )
    for contract in canceled_contracts:
        canceled_month_value += _contract_price(contract)

    payments_by_method = _sum_group(db, Payment.method, Payment.amount, Payment)
    titles_by_bank = _sum_group(db, Title.bank_code, Title.amount, Title)
    cnab = {
        "remittances": db.query(func.count(Remittance.id)).scalar() or 0,
        "returns": db.query(func.count(ReturnFile.id)).scalar() or 0,
        "returns_pending": db.query(func.count(ReturnFile.id)).filter(ReturnFile.processed_at.is_(None)).scalar() or 0,
    }
    gateway_status = _count_group(db, PaymentCharge.status, PaymentCharge)

    assignments_total = db.query(func.count(ContractNetworkAssignment.id)).scalar() or 0
    assignments_active = db.query(func.count(ContractNetworkAssignment.id)).filter(ContractNetworkAssignment.status == "active").scalar() or 0
    assignments_blocked = db.query(func.count(ContractNetworkAssignment.id)).filter(ContractNetworkAssignment.status == "blocked").scalar() or 0
    olt_total = db.query(func.count(NetworkDevice.id)).filter(NetworkDevice.type == "olt").scalar() or 0
    zabbix_monitored = db.query(func.count(NetworkDevice.id)).filter(NetworkDevice.zabbix_monitored == True).scalar() or 0
    zabbix_synced = db.query(func.count(NetworkDevice.id)).filter(NetworkDevice.zabbix_host_id.isnot(None)).scalar() or 0
    radius_active = db.query(func.count(RadAcct.radacctid)).filter(RadAcct.acctstoptime.is_(None)).scalar() or 0
    traffic_by_nas = [
        {"label": row[0] or "-", "value": round(((row[1] or 0) + (row[2] or 0)) / 1024 / 1024 / 1024, 2)}
        for row in db.query(RadAcct.nasipaddress, func.sum(RadAcct.acctinputoctets), func.sum(RadAcct.acctoutputoctets)).group_by(RadAcct.nasipaddress).limit(8).all()
    ]
    pool_usage = []
    for pool in db.query(IPPool).order_by(IPPool.name.asc()).limit(12).all():
        allocated = db.query(func.count(IPLease.id)).filter(IPLease.pool_id == pool.id, IPLease.status == "allocated").scalar() or 0
        try:
            capacity = max(ip_network(pool.cidr, strict=False).num_addresses - 2, 1)
        except ValueError:
            capacity = max(allocated, 1)
        pool_usage.append({"label": pool.name, "allocated": allocated, "capacity": capacity, "percent": round(allocated / capacity * 100, 1)})

    service_orders_by_status = _count_group(db, ServiceOrder.status, ServiceOrder)
    service_orders_by_tech = _count_group(db, ServiceOrder.technician_name, ServiceOrder, limit=8)
    completed_orders = db.query(ServiceOrder).filter(ServiceOrder.status == "completed", ServiceOrder.executed_at.isnot(None)).all()
    mttr_hours_values = [(o.executed_at - o.created_at).total_seconds() / 3600 for o in completed_orders if o.created_at and o.executed_at]
    mttr_hours = round(sum(mttr_hours_values) / len(mttr_hours_values), 1) if mttr_hours_values else 0.0
    backlog_open = db.query(ServiceOrder).filter(ServiceOrder.status.in_(["open", "scheduled", "in_progress"])).all()
    backlog_aging = {"0-2d": 0, "3-7d": 0, "8-15d": 0, "15d+": 0}
    for order in backlog_open:
        days = (now - order.created_at).days if order.created_at else 0
        bucket = "0-2d" if days <= 2 else "3-7d" if days <= 7 else "8-15d" if days <= 15 else "15d+"
        backlog_aging[bucket] += 1
    recurrence_clients = (
        db.query(ServiceOrder.client_id, func.count(ServiceOrder.id).label("total"))
        .filter(ServiceOrder.client_id.isnot(None))
        .group_by(ServiceOrder.client_id)
        .having(func.count(ServiceOrder.id) > 1)
        .count()
    )

    contract_status = _count_group(db, Contract.status, Contract)
    plan_mix = [
        {"label": row[0] or "-", "value": row[1]}
        for row in db.query(Plan.name, func.count(Contract.id)).join(Contract, Contract.plan_id == Plan.id).group_by(Plan.name).order_by(func.count(Contract.id).desc()).limit(8).all()
    ]
    client_status = _count_group(db, Client.status, Client)
    net_adds = [
        {"label": a["label"], "value": a["value"] - c["value"]}
        for a, c in zip(activations_monthly, cancellations_monthly)
    ]

    tickets_by_category = [
        {"label": row[0] or "-", "value": row[1]}
        for row in db.query(TicketCategory.name, func.count(Ticket.id)).join(Ticket, Ticket.category_id == TicketCategory.id).group_by(TicketCategory.name).all()
    ]
    ticket_status = _count_group(db, Ticket.status, Ticket)
    tickets_open = db.query(Ticket).filter(Ticket.status.in_(["open", "in_progress", "pending"])).count()
    sla_overdue = db.query(Ticket).filter(Ticket.status.in_(["open", "in_progress", "pending"]), Ticket.sla_due_at.isnot(None), Ticket.sla_due_at < now).count()
    first_response_hours = _avg_first_response_hours(db, Ticket, TicketMessage)
    reopen_rate = 0.0
    support_by_origin = _count_group(db, Ticket.origin, Ticket)

    warehouse_balance = []
    critical_items = 0
    for item in db.query(StockItem).filter(StockItem.is_active == True).all():
        in_qty = db.query(func.sum(StockMovement.quantity)).filter(StockMovement.item_id == item.id, StockMovement.type == "in").scalar() or 0
        out_qty = db.query(func.sum(StockMovement.quantity)).filter(StockMovement.item_id == item.id, StockMovement.type == "out").scalar() or 0
        if float(in_qty) - float(out_qty) <= float(item.min_qty or 0):
            critical_items += 1
    for warehouse in db.query(Warehouse).order_by(Warehouse.name.asc()).limit(10).all():
        in_qty = db.query(func.sum(StockMovement.quantity)).filter(StockMovement.warehouse_id == warehouse.id, StockMovement.type == "in").scalar() or 0
        out_qty = db.query(func.sum(StockMovement.quantity)).filter(StockMovement.warehouse_id == warehouse.id, StockMovement.type == "out").scalar() or 0
        warehouse_balance.append({"label": warehouse.name, "value": float(in_qty) - float(out_qty)})
    stock_movements = _count_group(db, StockMovement.type, StockMovement)
    comodato_status = _count_group(db, Comodato.status, Comodato)
    comodato_top_clients = [
        {"label": f"Cliente {row[0]}", "value": row[1]}
        for row in db.query(Comodato.client_id, func.count(Comodato.id)).group_by(Comodato.client_id).order_by(func.count(Comodato.id).desc()).limit(8).all()
    ]

    invoice_status = _count_group(db, Invoice.status, Invoice)
    invoice_type_totals = _sum_group(db, Invoice.invoice_type, Invoice.total_amount, Invoice)
    fiscal_pending = {
        "draft_invoices": db.query(func.count(Invoice.id)).filter(Invoice.status == "draft").scalar() or 0,
        "plans_without_fiscal_detail": max((db.query(func.count(Plan.id)).scalar() or 0) - (db.query(func.count(ServicePlanDetail.id)).scalar() or 0), 0),
    }

    communication_by_channel = _count_group(db, MessageQueue.channel, MessageQueue)
    communication_by_status = _count_group(db, MessageQueue.status, MessageQueue)
    communication_by_provider = communication_success_by_provider(db, days=30)
    communication_failures = _count_group(db, MessageQueue.provider, MessageQueue, status_filter=("failed",))

    return {
        "financial": {
            "mrr": round(mrr, 2),
            "arr": round(arr, 2),
            "dso": dso,
            "financial_churn": round(canceled_month_value, 2),
            "monthly_revenue": revenue_monthly,
            "aging": _dict_to_series(aging),
            "payments_by_method": payments_by_method,
            "titles_by_bank": titles_by_bank,
            "gateway_status": gateway_status,
            "cnab": cnab,
        },
        "network": {
            "assignments_total": assignments_total,
            "assignments_active": assignments_active,
            "assignments_blocked": assignments_blocked,
            "olt_total": olt_total,
            "zabbix_monitored": zabbix_monitored,
            "zabbix_synced": zabbix_synced,
            "radius_active": radius_active,
            "pool_usage": pool_usage,
            "traffic_by_nas": traffic_by_nas,
        },
        "operations": {
            "service_orders_by_status": service_orders_by_status,
            "service_orders_by_tech": service_orders_by_tech,
            "mttr_hours": mttr_hours,
            "backlog_aging": _dict_to_series(backlog_aging),
            "recurrence_clients": recurrence_clients,
        },
        "clients": {
            "contract_status": contract_status,
            "client_status": client_status,
            "activations": activations_monthly,
            "cancellations": cancellations_monthly,
            "net_adds": net_adds,
            "plan_mix": plan_mix,
        },
        "support": {
            "tickets_by_category": tickets_by_category,
            "ticket_status": ticket_status,
            "tickets_open": tickets_open,
            "sla_overdue": sla_overdue,
            "first_response_hours": first_response_hours,
            "reopen_rate": reopen_rate,
            "by_origin": support_by_origin,
        },
        "stock": {
            "warehouse_balance": warehouse_balance,
            "critical_items": critical_items,
            "stock_movements": stock_movements,
            "comodato_status": comodato_status,
            "comodato_top_clients": comodato_top_clients,
        },
        "fiscal": {
            "invoice_status": invoice_status,
            "invoice_type_totals": invoice_type_totals,
            "pending": fiscal_pending,
        },
        "communication": {
            "by_channel": communication_by_channel,
            "by_status": communication_by_status,
            "by_provider": communication_by_provider,
            "failures_by_provider": communication_failures,
        },
    }


def _month_starts(today: date, months: int) -> list[date]:
    starts = []
    for offset in range(months - 1, -1, -1):
        month_index = today.month - offset
        year = today.year + ((month_index - 1) // 12)
        month = ((month_index - 1) % 12) + 1
        starts.append(today.replace(year=year, month=month, day=1))
    return starts


def _next_month(day: date) -> date:
    month_index = day.month + 1
    year = day.year + ((month_index - 1) // 12)
    month = ((month_index - 1) % 12) + 1
    return day.replace(year=year, month=month, day=1)


def _contract_price(contract: Contract) -> float:
    if contract.price_override is not None:
        return float(contract.price_override)
    if contract.plan:
        return float(contract.plan.price or 0)
    return 0.0


def _count_group(db: Session, group_col, model, limit: int | None = None, status_filter: tuple[str, ...] | None = None) -> list[dict]:
    q = db.query(group_col, func.count(model.id))
    if status_filter and hasattr(model, "status"):
        q = q.filter(model.status.in_(status_filter))
    q = q.group_by(group_col).order_by(func.count(model.id).desc())
    if limit:
        q = q.limit(limit)
    return [{"label": row[0] or "-", "value": row[1]} for row in q.all()]


def _sum_group(db: Session, group_col, value_col, model, limit: int | None = None) -> list[dict]:
    q = db.query(group_col, func.sum(value_col)).group_by(group_col).order_by(func.sum(value_col).desc())
    if limit:
        q = q.limit(limit)
    return [{"label": row[0] or "-", "value": float(row[1] or 0)} for row in q.all()]


def _dict_to_series(values: dict) -> list[dict]:
    return [{"label": key, "value": value} for key, value in values.items()]


def _avg_first_response_hours(db: Session, TicketModel, MessageModel) -> float:
    tickets = db.query(TicketModel).filter(TicketModel.created_at.isnot(None)).limit(500).all()
    values = []
    for ticket in tickets:
        first = (
            db.query(MessageModel)
            .filter(MessageModel.ticket_id == ticket.id, MessageModel.created_at > ticket.created_at)
            .order_by(MessageModel.created_at.asc())
            .first()
        )
        if first:
            values.append((first.created_at - ticket.created_at).total_seconds() / 3600)
    return round(sum(values) / len(values), 1) if values else 0.0
