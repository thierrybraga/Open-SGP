"""
Arquivo: app/modules/support/service.py

Responsabilidade:
Lógica de negócios para suporte: criação de tickets, geração de protocolos,
fluxo de status, adição de mensagens.

Integrações:
- modules.support.models
- modules.support.schemas
"""

from sqlalchemy.orm import Session
from datetime import datetime
import random
import string

from .models import Ticket, TicketCategory, TicketMessage, Occurrence
from .schemas import TicketCreate, TicketUpdate, MessageCreate, CategoryCreate, OccurrenceCreate, OccurrenceUpdate

def generate_protocol() -> str:
    """Gera um número de protocolo único (ex: 202310270001)"""
    now = datetime.now()
    prefix = now.strftime("%Y%m%d")
    # In a real scenario, we would use a sequence or check for collisions
    # Here we use a random suffix for simplicity
    suffix = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{suffix}"

def create_category(db: Session, data: CategoryCreate) -> TicketCategory:
    cat = TicketCategory(**data.dict())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

def get_categories(db: Session, active_only: bool = True):
    query = db.query(TicketCategory)
    if active_only:
        query = query.filter(TicketCategory.is_active == True)
    return query.all()

def create_ticket(db: Session, data: TicketCreate) -> Ticket:
    ticket = Ticket(**data.dict())
    ticket.protocol = generate_protocol()
    ticket.status = "open"
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

def update_ticket(db: Session, ticket_id: int, data: TicketUpdate) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None
    
    if data.category_id is not None:
        ticket.category_id = data.category_id
    if data.assignee_id is not None:
        ticket.assignee_id = data.assignee_id
    if data.subject is not None:
        ticket.subject = data.subject
    if data.priority is not None:
        ticket.priority = data.priority
    if data.status is not None:
        ticket.status = data.status
        if data.status in ["closed", "canceled"] and not ticket.closed_at:
            ticket.closed_at = datetime.utcnow()
        if data.status not in ["closed", "canceled"]:
            ticket.closed_at = None
            
    db.commit()
    db.refresh(ticket)
    return ticket

def add_message(db: Session, data: MessageCreate) -> TicketMessage:
    msg = TicketMessage(**data.dict())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_ticket_messages(db: Session, ticket_id: int):
    return db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.created_at.asc()).all()

def create_occurrence(db: Session, data: OccurrenceCreate) -> Occurrence:
    occ = Occurrence(**data.dict())
    occ.status = "open"
    db.add(occ)
    db.commit()
    db.refresh(occ)
    return occ

def update_occurrence(db: Session, occurrence: Occurrence, data: OccurrenceUpdate) -> Occurrence:
    if data.category:
        occurrence.category = data.category
    if data.severity:
        occurrence.severity = data.severity
    if data.description:
        occurrence.description = data.description
    if data.status:
        occurrence.status = data.status
    if data.closed_at:
        occurrence.closed_at = data.closed_at
    if data.ticket_id is not None:
        occurrence.ticket_id = data.ticket_id
    if data.service_order_id is not None:
        occurrence.service_order_id = data.service_order_id
        
    db.commit()
    db.refresh(occurrence)
    return occurrence
