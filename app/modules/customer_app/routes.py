"""
Arquivo: app/modules/customer_app/routes.py

Responsabilidade:
Rotas REST do App do Cliente: perfil, contratos, títulos, preferências, tokens e
abertura de tickets.

Integrações:
- core.dependencies
- modules.customer_app.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, get_current_user, require_permissions
from ..users.models import User
from .schemas import (
    ProfileOut,
    ContractOut,
    TitleOut,
    PreferenceUpdate,
    PreferenceOut,
    DeviceTokenCreate,
    DeviceTokenOut,
    TicketCreate,
    TicketOut,
    CustomerLogin,
    Token,
)
from .service import (
    get_client_by_email,
    compute_profile,
    list_contracts,
    list_titles,
    upsert_preferences,
    register_token,
    open_ticket,
    authenticate_client,
)
from ...core.security import create_access_token


router = APIRouter()


@router.post("/auth/login", response_model=Token)
def login(data: CustomerLogin, db: Session = Depends(get_db)):
    client = authenticate_client(db, data.username, data.password)
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    
    # Create access token with subject=email and role=customer
    # We use a special scope/claim for customer app to differentiate from admin users
    token = create_access_token(
        subject=client.email,
        claims={"type": "customer", "client_id": client.id}
    )
    return Token(access_token=token, token_type="bearer")


@router.get("/profile", response_model=ProfileOut, dependencies=[Depends(require_permissions("customer.profile.read"))])
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = get_client_by_email(db, user.email)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado para o usuário")
    return compute_profile(db, client)


@router.get("/contracts", response_model=List[ContractOut], dependencies=[Depends(require_permissions("customer.contracts.read"))])
def get_contracts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = get_client_by_email(db, user.email)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado para o usuário")
    items = list_contracts(db, client.id)
    return [ContractOut(**i.__dict__) for i in items]


@router.get("/billing/titles", response_model=List[TitleOut], dependencies=[Depends(require_permissions("customer.billing.read"))])
def get_titles(status: Optional[str] = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = get_client_by_email(db, user.email)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado para o usuário")
    items = list_titles(db, client.id, status)
    return [TitleOut(**t.__dict__) for t in items]


@router.put("/preferences", response_model=PreferenceOut, dependencies=[Depends(require_permissions("customer.preferences.update"))])
def update_preferences(data: PreferenceUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = get_client_by_email(db, user.email)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado para o usuário")
    pref = upsert_preferences(db, client.id, data)
    return PreferenceOut(**pref.__dict__)


@router.post("/notifications/tokens", response_model=DeviceTokenOut, dependencies=[Depends(require_permissions("customer.notifications.register"))])
def register_notification_token(data: DeviceTokenCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = get_client_by_email(db, user.email)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado para o usuário")
    tok = register_token(db, client.id, data)
    return DeviceTokenOut(**tok.__dict__)


@router.post("/support/tickets", response_model=TicketOut, dependencies=[Depends(require_permissions("customer.support.create"))])
def create_ticket(data: TicketCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = get_client_by_email(db, user.email)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado para o usuário")
    t = open_ticket(db, client.id, data)
    return TicketOut(**t.__dict__)

