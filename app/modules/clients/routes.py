"""
Arquivo: app/modules/clients/routes.py

Responsabilidade:
Rotas REST para clientes, com filtros por nome, documento e cidade.

Integrações:
- core.dependencies
- modules.clients.service
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions, get_current_user
from .models import Client, ClientAddress
from .schemas import ClientCreate, ClientUpdate, ClientOut, AddressOut, ContactOut
from .service import create_client, update_client


router = APIRouter()


@router.get("/", response_model=List[ClientOut])
def list_clients(
    name: Optional[str] = Query(default=None),
    document: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Client)
    if name:
        q = q.filter(Client.name.ilike(f"%{name}%"))
    if document:
        q = q.filter(Client.document == document)
    if city:
        q = q.join(ClientAddress).filter(ClientAddress.city.ilike(f"%{city}%"))
    clients = q.all()
    out: List[ClientOut] = []
    for c in clients:
        out.append(
            ClientOut(
                id=c.id,
                person_type=c.person_type,
                name=c.name,
                document=c.document,
                email=c.email,
                phone=c.phone,
                is_active=c.is_active,
                addresses=[AddressOut(**a.__dict__) for a in c.addresses],
                contacts=[ContactOut(**ct.__dict__) for ct in c.contacts],
            )
        )
    return out


@router.post("/", response_model=ClientOut, dependencies=[Depends(require_permissions("clients.create"))])
def create_client_endpoint(data: ClientCreate, db: Session = Depends(get_db)):
    if db.query(Client).filter(Client.document == data.document).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client document already exists")
    if db.query(Client).filter(Client.email == data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client email already exists")
    c = create_client(db, data)
    return ClientOut(
        id=c.id,
        person_type=c.person_type,
        name=c.name,
        document=c.document,
        email=c.email,
        phone=c.phone,
        is_active=c.is_active,
        addresses=[AddressOut(**a.__dict__) for a in c.addresses],
        contacts=[ContactOut(**ct.__dict__) for ct in c.contacts],
    )


@router.put("/{client_id}", response_model=ClientOut, dependencies=[Depends(require_permissions("clients.update"))])
def update_client_endpoint(client_id: int, data: ClientUpdate, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    c = update_client(db, c, data)
    return ClientOut(
        id=c.id,
        person_type=c.person_type,
        name=c.name,
        document=c.document,
        email=c.email,
        phone=c.phone,
        is_active=c.is_active,
        addresses=[AddressOut(**a.__dict__) for a in c.addresses],
        contacts=[ContactOut(**ct.__dict__) for ct in c.contacts],
    )


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return ClientOut(
        id=c.id,
        person_type=c.person_type,
        name=c.name,
        document=c.document,
        email=c.email,
        phone=c.phone,
        is_active=c.is_active,
        addresses=[AddressOut(**a.__dict__) for a in c.addresses],
        contacts=[ContactOut(**ct.__dict__) for ct in c.contacts],
    )


@router.post("/{client_id}/approve", response_model=ClientOut, dependencies=[Depends(require_permissions("clients.approve"))])
def approve_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Aprova um cliente em pré-cadastro.
    """
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if c.status != "pre_registered":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client is not in pre-registered status")

    c.status = "active"
    c.approved_by = current_user.id
    c.approved_at = datetime.utcnow().isoformat()
    db.add(c)
    db.commit()
    db.refresh(c)

    return ClientOut(
        id=c.id,
        person_type=c.person_type,
        name=c.name,
        document=c.document,
        email=c.email,
        phone=c.phone,
        is_active=c.is_active,
        addresses=[AddressOut(**a.__dict__) for a in c.addresses],
        contacts=[ContactOut(**ct.__dict__) for ct in c.contacts],
    )


@router.post("/{client_id}/reject", dependencies=[Depends(require_permissions("clients.approve"))])
def reject_client(client_id: int, reason: str, db: Session = Depends(get_db)):
    """
    Rejeita um cliente em pré-cadastro.
    """
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if c.status != "pre_registered":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client is not in pre-registered status")

    c.status = "inactive"
    c.is_active = False
    db.add(c)
    db.commit()

    return {"message": f"Client rejected: {reason}"}


# ===== DASHBOARD =====

@router.get("/dashboard/summary")
def get_clients_dashboard_summary(db: Session = Depends(get_db)):
    """
    Retorna resumo estatístico de clientes.
    """
    from .dashboard import get_clients_summary
    return get_clients_summary(db)


@router.get("/dashboard/by-city")
def get_clients_by_city_stats(
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db)
):
    """
    Retorna top cidades com mais clientes.
    """
    from .dashboard import get_clients_by_city
    return get_clients_by_city(db, limit)


@router.get("/dashboard/by-state")
def get_clients_by_state_stats(db: Session = Depends(get_db)):
    """
    Retorna clientes agrupados por estado.
    """
    from .dashboard import get_clients_by_state
    return get_clients_by_state(db)


@router.get("/dashboard/recent")
def get_recent_clients_list(
    days: int = Query(default=30, le=365),
    limit: int = Query(default=10, le=100),
    db: Session = Depends(get_db)
):
    """
    Retorna clientes cadastrados recentemente.
    """
    from .dashboard import get_recent_clients
    clients = get_recent_clients(db, days, limit)
    return [
        {
            "id": c.id,
            "name": c.name,
            "document": c.document,
            "email": c.email,
            "status": c.status,
            "created_at": c.created_at
        }
        for c in clients
    ]


@router.get("/dashboard/growth")
def get_clients_growth_stats(
    months: int = Query(default=12, le=24),
    db: Session = Depends(get_db)
):
    """
    Retorna crescimento de clientes nos últimos meses.
    """
    from .dashboard import get_clients_growth
    return get_clients_growth(db, months)


@router.get("/dashboard/debt")
def get_clients_debt_stats(db: Session = Depends(get_db)):
    """
    Retorna estatísticas de clientes com dívidas.
    """
    from .dashboard import get_clients_with_debt
    return get_clients_with_debt(db)


@router.get("/dashboard/top-revenue")
def get_top_clients_revenue(
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db)
):
    """
    Retorna top clientes por receita.
    """
    from .dashboard import get_top_clients_by_revenue
    return get_top_clients_by_revenue(db, limit)


@router.get("/dashboard/complete")
def get_complete_dashboard(db: Session = Depends(get_db)):
    """
    Retorna dashboard completo de clientes com todas as estatísticas.
    """
    from .dashboard import get_clients_dashboard_complete
    return get_clients_dashboard_complete(db)

