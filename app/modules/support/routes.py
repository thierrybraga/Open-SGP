"""
Arquivo: app/modules/support/routes.py

Responsabilidade:
Rotas REST para suporte: tickets, mensagens e ocorrências.

Integrações:
- core.dependencies
- modules.support.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Ticket, TicketMessage, Occurrence
from .schemas import (
    TicketCreate,
    TicketUpdate,
    TicketOut,
    MessageCreate,
    MessageOut,
    OccurrenceCreate,
    OccurrenceUpdate,
    OccurrenceOut,
)
from .service import create_ticket, add_message, update_ticket, create_occurrence, update_occurrence


router = APIRouter()


@router.get("/tickets", response_model=List[TicketOut])
def list_tickets(
    status_: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = Query(default=None),
    contract_id: Optional[int] = Query(default=None),
    client_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Ticket)
    if status_:
        q = q.filter(Ticket.status == status_)
    if priority:
        q = q.filter(Ticket.priority == priority)
    if contract_id:
        q = q.filter(Ticket.contract_id == contract_id)
    if client_id:
        q = q.filter(Ticket.client_id == client_id)
    items = q.all()
    # Pydantic's from_attributes=True handles the conversion from ORM objects
    return items


@router.post("/tickets", response_model=TicketOut, dependencies=[Depends(require_permissions("support.tickets.create"))])
def create_ticket_endpoint(data: TicketCreate, db: Session = Depends(get_db)):
    t = create_ticket(db, data)
    return t


@router.put("/tickets/{ticket_id}", response_model=TicketOut, dependencies=[Depends(require_permissions("support.tickets.update"))])
def update_ticket_endpoint(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    t = update_ticket(db, t, data)
    return t


@router.post("/tickets/{ticket_id}/messages", response_model=MessageOut, dependencies=[Depends(require_permissions("support.messages.create"))])
def add_message_endpoint(ticket_id: int, data: MessageCreate, db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    m = add_message(db, t, data)
    return m


@router.get("/occurrences", response_model=List[OccurrenceOut])
def list_occurrences(
    status_: Optional[str] = Query(default=None, alias="status"),
    severity: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    contract_id: Optional[int] = Query(default=None),
    client_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Occurrence)
    if status_:
        q = q.filter(Occurrence.status == status_)
    if severity:
        q = q.filter(Occurrence.severity == severity)
    if category:
        q = q.filter(Occurrence.category == category)
    if contract_id:
        q = q.filter(Occurrence.contract_id == contract_id)
    if client_id:
        q = q.filter(Occurrence.client_id == client_id)
    items = q.order_by(Occurrence.created_at.desc()).limit(200).all()
    return items


@router.post("/occurrences", response_model=OccurrenceOut, dependencies=[Depends(require_permissions("support.occurrences.create"))])
def create_occurrence_endpoint(data: OccurrenceCreate, db: Session = Depends(get_db)):
    o = create_occurrence(db, data)
    return o


@router.put("/occurrences/{occurrence_id}", response_model=OccurrenceOut, dependencies=[Depends(require_permissions("support.occurrences.update"))])
def update_occurrence_endpoint(occurrence_id: int, data: OccurrenceUpdate, db: Session = Depends(get_db)):
    o = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Occurrence not found")
    o = update_occurrence(db, o, data)
    return o


@router.get("/occurrences/{occurrence_id}", response_model=OccurrenceOut)
def get_occurrence_endpoint(occurrence_id: int, db: Session = Depends(get_db)):
    o = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Occurrence not found")
    return o
