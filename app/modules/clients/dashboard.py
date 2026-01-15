"""
Arquivo: app/modules/clients/dashboard.py

Responsabilidade:
Dashboard e estatísticas de clientes.

Integrações:
- modules.clients.models
- modules.contracts.models
- modules.billing.models
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta

from .models import Client
from ..contracts.models import Contract
from ..billing.models import Title


def get_clients_summary(db: Session) -> dict:
    """
    Retorna resumo geral de clientes.
    """
    # Total de clientes
    total_clients = db.query(func.count(Client.id)).scalar()

    # Clientes ativos
    active_clients = db.query(func.count(Client.id)).filter(
        Client.status == "active"
    ).scalar()

    # Clientes pré-cadastrados
    pre_registered = db.query(func.count(Client.id)).filter(
        Client.status == "pre_registered"
    ).scalar()

    # Clientes inativos
    inactive_clients = db.query(func.count(Client.id)).filter(
        Client.status == "inactive"
    ).scalar()

    # Clientes por tipo
    pf_count = db.query(func.count(Client.id)).filter(
        Client.person_type == "PF"
    ).scalar()

    pj_count = db.query(func.count(Client.id)).filter(
        Client.person_type == "PJ"
    ).scalar()

    # Clientes com contratos ativos
    with_contracts = db.query(func.count(func.distinct(Contract.client_id))).filter(
        Contract.status == "active"
    ).scalar()

    return {
        "total_clients": total_clients or 0,
        "active_clients": active_clients or 0,
        "pre_registered": pre_registered or 0,
        "inactive_clients": inactive_clients or 0,
        "pf_count": pf_count or 0,
        "pj_count": pj_count or 0,
        "with_active_contracts": with_contracts or 0
    }


def get_clients_by_city(db: Session, limit: int = 10) -> list:
    """
    Retorna top cidades com mais clientes.
    """
    results = db.query(
        Client.city,
        func.count(Client.id).label('count')
    ).filter(
        Client.city.isnot(None)
    ).group_by(
        Client.city
    ).order_by(
        func.count(Client.id).desc()
    ).limit(limit).all()

    return [{"city": r.city, "count": r.count} for r in results]


def get_clients_by_state(db: Session) -> list:
    """
    Retorna clientes agrupados por estado.
    """
    results = db.query(
        Client.state,
        func.count(Client.id).label('count')
    ).filter(
        Client.state.isnot(None)
    ).group_by(
        Client.state
    ).order_by(
        func.count(Client.id).desc()
    ).all()

    return [{"state": r.state, "count": r.count} for r in results]


def get_recent_clients(db: Session, days: int = 30, limit: int = 10) -> list:
    """
    Retorna clientes cadastrados recentemente.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    clients = db.query(Client).filter(
        Client.created_at >= cutoff_date.isoformat()
    ).order_by(
        Client.created_at.desc()
    ).limit(limit).all()

    return clients


def get_clients_growth(db: Session, months: int = 12) -> list:
    """
    Retorna crescimento de clientes nos últimos meses.
    """
    # Esta é uma implementação simplificada
    # Em produção, usar queries mais otimizadas com window functions
    results = []

    for i in range(months):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)

        count = db.query(func.count(Client.id)).filter(
            Client.created_at >= month_start.isoformat(),
            Client.created_at < month_end.isoformat()
        ).scalar()

        results.append({
            "month": month_start.strftime("%Y-%m"),
            "count": count or 0
        })

    return list(reversed(results))


def get_clients_with_debt(db: Session) -> dict:
    """
    Retorna estatísticas de clientes com dívidas.
    """
    # Clientes com títulos em aberto
    clients_with_open_titles = db.query(
        func.count(func.distinct(Title.contract_id))
    ).join(
        Contract, Title.contract_id == Contract.id
    ).filter(
        Title.status == "open"
    ).scalar()

    # Clientes com títulos vencidos
    today = datetime.utcnow().date()
    clients_with_overdue = db.query(
        func.count(func.distinct(Title.contract_id))
    ).join(
        Contract, Title.contract_id == Contract.id
    ).filter(
        Title.status == "open",
        Title.due_date < today
    ).scalar()

    # Total em aberto
    total_open = db.query(
        func.sum(Title.amount)
    ).filter(
        Title.status == "open"
    ).scalar()

    # Total vencido
    total_overdue = db.query(
        func.sum(Title.amount)
    ).filter(
        Title.status == "open",
        Title.due_date < today
    ).scalar()

    return {
        "clients_with_open_titles": clients_with_open_titles or 0,
        "clients_with_overdue": clients_with_overdue or 0,
        "total_open_amount": float(total_open) if total_open else 0.0,
        "total_overdue_amount": float(total_overdue) if total_overdue else 0.0
    }


def get_top_clients_by_revenue(db: Session, limit: int = 10) -> list:
    """
    Retorna top clientes por receita (títulos pagos).
    """
    results = db.query(
        Client.id,
        Client.name,
        func.sum(Title.amount).label('total_revenue')
    ).join(
        Contract, Client.id == Contract.client_id
    ).join(
        Title, Contract.id == Title.contract_id
    ).filter(
        Title.status == "paid"
    ).group_by(
        Client.id, Client.name
    ).order_by(
        func.sum(Title.amount).desc()
    ).limit(limit).all()

    return [
        {
            "client_id": r.id,
            "client_name": r.name,
            "total_revenue": float(r.total_revenue)
        }
        for r in results
    ]


def get_clients_dashboard_complete(db: Session) -> dict:
    """
    Retorna dashboard completo de clientes.
    """
    return {
        "summary": get_clients_summary(db),
        "by_city": get_clients_by_city(db, limit=10),
        "by_state": get_clients_by_state(db),
        "recent_clients": [
            {
                "id": c.id,
                "name": c.name,
                "document": c.document,
                "created_at": c.created_at
            }
            for c in get_recent_clients(db, days=30, limit=10)
        ],
        "growth": get_clients_growth(db, months=12),
        "debt_stats": get_clients_with_debt(db),
        "top_clients": get_top_clients_by_revenue(db, limit=10)
    }
