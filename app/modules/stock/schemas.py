"""
Arquivo: app/modules/stock/schemas.py

Responsabilidade:
Esquemas Pydantic para Estoque: itens, almoxarifados, movimentos e saldos.

Integrações:
- modules.stock.models
"""

from typing import Optional
from pydantic import BaseModel


class WarehouseCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseOut(BaseModel):
    id: int
    name: str
    code: str
    address: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class StockItemCreate(BaseModel):
    name: str
    code: str
    unit: str
    min_qty: float = 0.0
    is_active: bool = True


class StockItemUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    min_qty: Optional[float] = None
    is_active: Optional[bool] = None


class StockItemOut(BaseModel):
    id: int
    name: str
    code: str
    unit: str
    min_qty: float
    is_active: bool

    class Config:
        from_attributes = True


class MovementCreate(BaseModel):
    item_id: int
    warehouse_id: int
    type: str
    quantity: float
    unit_cost: Optional[float] = None
    note: Optional[str] = None


class MovementOut(BaseModel):
    id: int
    item_id: int
    warehouse_id: int
    type: str
    quantity: float
    unit_cost: Optional[float]
    total_value: Optional[float]
    note: Optional[str]

    class Config:
        from_attributes = True


class StockBalance(BaseModel):
    item_id: int
    warehouse_id: Optional[int]
    quantity: float


class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ManufacturerCreate(BaseModel):
    name: str


class ManufacturerOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SupplierCreate(BaseModel):
    name: str
    document: str
    person_type: str  # PF ou PJ
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    contact_person: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    contact_person: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierOut(BaseModel):
    id: int
    name: str
    document: str
    person_type: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    contact_person: Optional[str]
    payment_terms: Optional[str]
    notes: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class VehicleCreate(BaseModel):
    plate: str
    description: str
    is_active: bool = True


class VehicleOut(BaseModel):
    id: int
    plate: str
    description: str
    is_active: bool

    class Config:
        from_attributes = True


class KitCreate(BaseModel):
    name: str
    description: str


class KitOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class PurchaseCreate(BaseModel):
    supplier_id: Optional[int] = None
    supplier_name: str
    document_number: str


class PurchaseItemCreate(BaseModel):
    purchase_id: int
    item_id: int
    quantity: float
    unit_cost: float
    warehouse_id: int


class PurchaseOut(BaseModel):
    id: int
    supplier_name: str
    document_number: str
    total_value: float

    class Config:
        from_attributes = True


class TransferCreate(BaseModel):
    from_warehouse_id: int
    to_warehouse_id: int
    note: Optional[str] = None


class TransferItemCreate(BaseModel):
    transfer_id: int
    item_id: int
    quantity: float


class KitItemCreate(BaseModel):
    kit_id: int
    item_id: int
    quantity: float


class AdjustmentCreate(BaseModel):
    item_id: int
    warehouse_id: int
    type: str
    quantity: float
    reason: str
    ref_document: Optional[str] = None


class AdjustmentOut(BaseModel):
    id: int
    item_id: int
    warehouse_id: int
    type: str
    quantity: float
    reason: str
    ref_document: Optional[str]

    class Config:
        from_attributes = True


class TransferOut(BaseModel):
    id: int
    from_warehouse_id: int
    to_warehouse_id: int
    note: Optional[str]

    class Config:
        from_attributes = True


class NFeImportRequest(BaseModel):
    xml_content: str
    warehouse_id: int
    create_missing_items: bool = False


class NFeImportOut(BaseModel):
    purchase_id: int
    document_number: str
    supplier_name: str
    items_imported: int


# ===== COMODATO =====

class ComodatoCreate(BaseModel):
    client_id: int
    contract_id: Optional[int] = None
    item_id: int
    warehouse_id: int
    serial_number: Optional[str] = None
    quantity: float = 1.0
    loan_date: str
    expected_return_date: Optional[str] = None
    declared_value: float = 0.0
    loan_notes: Optional[str] = None


class ComodatoUpdate(BaseModel):
    status: Optional[str] = None
    return_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    return_notes: Optional[str] = None


class ComodatoOut(BaseModel):
    id: int
    client_id: int
    contract_id: Optional[int] = None
    item_id: int
    warehouse_id: int
    serial_number: Optional[str] = None
    quantity: float
    status: str
    loan_date: str
    return_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    declared_value: float
    loan_notes: Optional[str] = None
    return_notes: Optional[str] = None

    class Config:
        from_attributes = True
