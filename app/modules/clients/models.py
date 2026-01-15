"""
Arquivo: app/modules/clients/models.py

Responsabilidade:
Modelos de Clientes, Endereços e Contatos com relacionamentos e índices.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_type: Mapped[str] = mapped_column(String(2))  # PF/PJ
    name: Mapped[str] = mapped_column(String(150), index=True)
    document: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # CPF/CNPJ
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status do cadastro
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)  # pre_registered, active, inactive, suspended
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    addresses = relationship("ClientAddress", back_populates="client", cascade="all, delete-orphan")
    contacts = relationship("ClientContact", back_populates="client", cascade="all, delete-orphan")
    viabilities = relationship("Viability", back_populates="client")

    __table_args__ = ()


class ClientAddress(Base, TimestampMixin):
    __tablename__ = "client_addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    street: Mapped[str] = mapped_column(String(255))
    number: Mapped[str] = mapped_column(String(20))
    neighborhood: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(120), index=True)
    state: Mapped[str] = mapped_column(String(2))
    zipcode: Mapped[str] = mapped_column(String(20))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    client = relationship("Client", back_populates="addresses")


class ClientContact(Base, TimestampMixin):
    __tablename__ = "client_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(80))

    client = relationship("Client", back_populates="contacts")
