"""
Arquivo: app/modules/stock/models.py

Responsabilidade:
Modelos de Estoque: Itens, Almoxarifados e Movimentos com relacionamentos e
campos auditáveis.

Integrações:
- core.database
- shared.models
"""

from sqlalchemy import String, Integer, Float, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base
from ...shared.models import TimestampMixin


class Warehouse(Base, TimestampMixin):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(30), unique=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StockItem(Base, TimestampMixin):
    __tablename__ = "stock_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    unit: Mapped[str] = mapped_column(String(20))
    min_qty: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = ()


class StockMovement(Base, TimestampMixin):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id", ondelete="CASCADE"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(10))  # in, out
    quantity: Mapped[float] = mapped_column(Float)
    unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    item = relationship("StockItem")
    warehouse = relationship("Warehouse")


class StockAdjustment(Base, TimestampMixin):
    __tablename__ = "stock_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id", ondelete="CASCADE"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(10))  # increase, decrease
    quantity: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(255))
    ref_document: Mapped[str | None] = mapped_column(String(100), nullable=True)


class StockCategory(Base, TimestampMixin):
    __tablename__ = "stock_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Manufacturer(Base, TimestampMixin):
    __tablename__ = "manufacturers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    document: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # CPF/CNPJ
    person_type: Mapped[str] = mapped_column(String(2))  # PF ou PJ
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plate: Mapped[str] = mapped_column(String(10), unique=True)
    description: Mapped[str] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Kit(Base, TimestampMixin):
    __tablename__ = "kits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(String(255))


class KitItem(Base, TimestampMixin):
    __tablename__ = "kit_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kit_id: Mapped[int] = mapped_column(ForeignKey("kits.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[float] = mapped_column(Float, default=1.0)


class Purchase(Base, TimestampMixin):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), index=True, nullable=True)
    supplier_name: Mapped[str] = mapped_column(String(150))  # Mantido para compatibilidade
    document_number: Mapped[str] = mapped_column(String(50), unique=True)
    total_value: Mapped[float] = mapped_column(Float, default=0.0)

    supplier = relationship("Supplier")


class PurchaseItem(Base, TimestampMixin):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    unit_cost: Mapped[float] = mapped_column(Float)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True)


class Transfer(Base, TimestampMixin):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True)
    to_warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TransferItem(Base, TimestampMixin):
    __tablename__ = "transfer_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transfer_id: Mapped[int] = mapped_column(ForeignKey("transfers.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[float] = mapped_column(Float)


class Comodato(Base, TimestampMixin):
    """
    Comodato: empréstimo gratuito de equipamento ao cliente.
    """
    __tablename__ = "comodatos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id", ondelete="RESTRICT"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), index=True)

    # Identificação única do equipamento (ex: número de série)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Quantidade emprestada
    quantity: Mapped[float] = mapped_column(Float, default=1.0)

    # Status: active, returned, lost, damaged
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)

    # Datas
    loan_date: Mapped[str] = mapped_column(String(30))  # Data do empréstimo
    return_date: Mapped[str | None] = mapped_column(String(30), nullable=True)  # Data da devolução
    expected_return_date: Mapped[str | None] = mapped_column(String(30), nullable=True)  # Previsão de devolução

    # Valores
    declared_value: Mapped[float] = mapped_column(Float, default=0.0)  # Valor declarado do equipamento

    # Observações
    loan_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    return_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relações
    client = relationship("Client")
    contract = relationship("Contract")
    item = relationship("StockItem")
    warehouse = relationship("Warehouse")
