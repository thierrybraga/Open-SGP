"""
Arquivo: app/modules/clients/service.py

Responsabilidade:
Regras de negócio para criação e atualização de clientes, incluindo endereços e contatos.

Integrações:
- modules.clients.models
"""

from sqlalchemy.orm import Session
from .models import Client, ClientAddress, ClientContact
from .schemas import ClientCreate, ClientUpdate, AddressIn, ContactIn


def _apply_addresses(client: Client, addresses: list[AddressIn]):
    client.addresses = [
        ClientAddress(
            street=a.street,
            number=a.number,
            neighborhood=a.neighborhood,
            city=a.city,
            state=a.state,
            zipcode=a.zipcode,
            is_primary=a.is_primary,
        )
        for a in addresses
    ]


def _apply_contacts(client: Client, contacts: list[ContactIn]):
    client.contacts = [
        ClientContact(name=c.name, phone=c.phone, email=c.email, role=c.role) for c in contacts
    ]


def create_client(db: Session, data: ClientCreate) -> Client:
    client = Client(
        person_type=data.person_type,
        name=data.name,
        document=data.document,
        email=data.email,
        phone=data.phone,
    )
    _apply_addresses(client, data.addresses)
    _apply_contacts(client, data.contacts)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, client: Client, data: ClientUpdate) -> Client:
    if data.name is not None:
        client.name = data.name
    if data.email is not None:
        client.email = data.email
    if data.phone is not None:
        client.phone = data.phone
    if data.is_active is not None:
        client.is_active = data.is_active
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

