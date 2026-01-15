"""
Arquivo: app/modules/customer_app/service.py

Responsabilidade:
Regras de negócio do App do Cliente: perfil, preferências, tokens, contratos,
títulos e criação de tickets.

Integrações:
- modules.customer_app.models
- modules.clients.models
- modules.contracts.models
- modules.billing.models
- modules.support.models
"""

from sqlalchemy.orm import Session

from .models import CustomerPreference, DeviceToken
from ..clients.models import Client
from ..contracts.models import Contract
from ..billing.models import Title
from ..support.models import Ticket
from .schemas import PreferenceUpdate, DeviceTokenCreate, TicketCreate
from ...core.security import verify_password


def authenticate_client(db: Session, email_or_doc: str, password: str) -> Client | None:
    # Try email
    client = db.query(Client).filter(Client.email == email_or_doc).first()
    if not client:
        # Try document
        client = db.query(Client).filter(Client.document == email_or_doc).first()
    
    if not client or not client.password_hash:
        return None
    
    if verify_password(password, client.password_hash):
        return client
    return None


def get_client_by_email(db: Session, email: str) -> Client | None:
    return db.query(Client).filter(Client.email == email).first()


def compute_profile(db: Session, client: Client) -> dict:
    contracts_active = db.query(Contract).filter(Contract.client_id == client.id, Contract.status == "active").count()
    overdue_titles = db.query(Title).join(Contract, Title.contract_id == Contract.id).filter(Contract.client_id == client.id, Title.status == "overdue").all()
    amount_overdue = sum(t.amount for t in overdue_titles)
    return {
        "client_id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "contracts_active": contracts_active,
        "titles_overdue": len(overdue_titles),
        "amount_overdue": float(amount_overdue),
    }


def list_contracts(db: Session, client_id: int) -> list[Contract]:
    return db.query(Contract).filter(Contract.client_id == client_id).all()


def list_titles(db: Session, client_id: int, status: str | None = None) -> list[Title]:
    q = db.query(Title).join(Contract, Title.contract_id == Contract.id).filter(Contract.client_id == client_id)
    if status:
        q = q.filter(Title.status == status)
    return q.all()


def upsert_preferences(db: Session, client_id: int, data: PreferenceUpdate) -> CustomerPreference:
    pref = db.query(CustomerPreference).filter(CustomerPreference.client_id == client_id).first()
    if not pref:
        pref = CustomerPreference(client_id=client_id)
    for field, value in data.dict(exclude_none=True).items():
        setattr(pref, field, value)
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


def register_token(db: Session, client_id: int, data: DeviceTokenCreate) -> DeviceToken:
    tok = DeviceToken(client_id=client_id, platform=data.platform, token=data.token)
    db.add(tok)
    db.commit()
    db.refresh(tok)
    return tok


def open_ticket(db: Session, client_id: int, data: TicketCreate) -> Ticket:
    t = Ticket(
        client_id=client_id,
        contract_id=data.contract_id,
        subject=data.subject,
        category=data.category,
        priority=data.priority,
        status="open",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

