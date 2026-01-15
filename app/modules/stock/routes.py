"""
Arquivo: app/modules/stock/routes.py

Responsabilidade:
Rotas REST para Estoque: itens, almoxarifados, movimentos e saldo de estoque.

Integrações:
- core.dependencies
- modules.stock.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Warehouse, StockItem, StockMovement, StockCategory, Manufacturer, Supplier, Vehicle, Kit, Purchase, Transfer, StockAdjustment, Comodato
from .schemas import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseOut,
    StockItemCreate,
    StockItemUpdate,
    StockItemOut,
    MovementCreate,
    MovementOut,
    StockBalance,
    CategoryCreate,
    CategoryOut,
    ManufacturerCreate,
    ManufacturerOut,
    SupplierCreate,
    SupplierUpdate,
    SupplierOut,
    VehicleCreate,
    VehicleOut,
    KitCreate,
    KitOut,
    PurchaseCreate,
    PurchaseOut,
    PurchaseItemCreate,
    TransferCreate,
    TransferOut,
    TransferItemCreate,
    AdjustmentCreate,
    AdjustmentOut,
    KitItemCreate,
    NFeImportRequest,
    NFeImportOut,
    ComodatoCreate,
    ComodatoUpdate,
    ComodatoOut,
)
from .service import (
    create_warehouse,
    update_warehouse,
    create_item,
    update_item,
    register_movement,
    get_balance,
    create_category,
    create_manufacturer,
    create_vehicle,
    create_kit,
    create_purchase,
    create_transfer,
    add_purchase_item,
    add_transfer_item,
    add_kit_item,
    register_adjustment,
    import_nfe_purchase,
    create_comodato,
    return_comodato,
    update_comodato_status,
    get_active_comodatos_by_client,
)


router = APIRouter()


@router.get("/warehouses", response_model=List[WarehouseOut], dependencies=[Depends(require_permissions("stock.warehouses.read"))])
def list_warehouses(db: Session = Depends(get_db)):
    items = db.query(Warehouse).all()
    return [WarehouseOut(**w.__dict__) for w in items]


@router.post("/warehouses", response_model=WarehouseOut, dependencies=[Depends(require_permissions("stock.warehouses.create"))])
def create_warehouse_endpoint(data: WarehouseCreate, db: Session = Depends(get_db)):
    w = create_warehouse(db, data)
    return WarehouseOut(**w.__dict__)


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseOut, dependencies=[Depends(require_permissions("stock.warehouses.update"))])
def update_warehouse_endpoint(warehouse_id: int, data: WarehouseUpdate, db: Session = Depends(get_db)):
    w = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    w = update_warehouse(db, w, data)
    return WarehouseOut(**w.__dict__)


@router.get("/items", response_model=List[StockItemOut], dependencies=[Depends(require_permissions("stock.items.read"))])
def list_items(db: Session = Depends(get_db)):
    items = db.query(StockItem).all()
    return [StockItemOut(**i.__dict__) for i in items]


@router.post("/items", response_model=StockItemOut, dependencies=[Depends(require_permissions("stock.items.create"))])
def create_item_endpoint(data: StockItemCreate, db: Session = Depends(get_db)):
    i = create_item(db, data)
    return StockItemOut(**i.__dict__)


@router.put("/items/{item_id}", response_model=StockItemOut, dependencies=[Depends(require_permissions("stock.items.update"))])
def update_item_endpoint(item_id: int, data: StockItemUpdate, db: Session = Depends(get_db)):
    i = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not i:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    i = update_item(db, i, data)
    return StockItemOut(**i.__dict__)


@router.get("/movements", response_model=List[MovementOut], dependencies=[Depends(require_permissions("stock.movements.read"))])
def list_movements(item_id: Optional[int] = None, warehouse_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(StockMovement)
    if item_id is not None:
        q = q.filter(StockMovement.item_id == item_id)
    if warehouse_id is not None:
        q = q.filter(StockMovement.warehouse_id == warehouse_id)
    return [MovementOut(**m.__dict__) for m in q.all()]


@router.post("/movements", response_model=MovementOut, dependencies=[Depends(require_permissions("stock.movements.create"))])
def register_movement_endpoint(data: MovementCreate, db: Session = Depends(get_db)):
    m = register_movement(db, data)
    return MovementOut(**m.__dict__)


@router.get("/stock/{item_id}/balance", response_model=StockBalance, dependencies=[Depends(require_permissions("stock.balance.read"))])
def stock_balance_endpoint(item_id: int, warehouse_id: Optional[int] = None, db: Session = Depends(get_db)):
    return get_balance(db, item_id=item_id, warehouse_id=warehouse_id)


# Categorias
@router.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    items = db.query(StockCategory).all()
    return [CategoryOut(**c.__dict__) for c in items]


@router.post("/categories", response_model=CategoryOut, dependencies=[Depends(require_permissions("stock.categories.create"))])
def create_category_endpoint(data: CategoryCreate, db: Session = Depends(get_db)):
    c = create_category(db, data)
    return CategoryOut(**c.__dict__)


# Fabricantes
@router.get("/manufacturers", response_model=List[ManufacturerOut])
def list_manufacturers(db: Session = Depends(get_db)):
    items = db.query(Manufacturer).all()
    return [ManufacturerOut(**m.__dict__) for m in items]


@router.post("/manufacturers", response_model=ManufacturerOut, dependencies=[Depends(require_permissions("stock.manufacturers.create"))])
def create_manufacturer_endpoint(data: ManufacturerCreate, db: Session = Depends(get_db)):
    m = create_manufacturer(db, data)
    return ManufacturerOut(**m.__dict__)


# Fornecedores
@router.get("/suppliers", response_model=List[SupplierOut])
def list_suppliers(
    active: Optional[bool] = Query(default=None),
    name: Optional[str] = Query(default=None),
    document: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    q = db.query(Supplier)
    if active is not None:
        q = q.filter(Supplier.is_active == active)
    if name:
        q = q.filter(Supplier.name.ilike(f"%{name}%"))
    if document:
        q = q.filter(Supplier.document == document)
    items = q.all()
    return [SupplierOut(**s.__dict__) for s in items]


@router.post("/suppliers", response_model=SupplierOut, dependencies=[Depends(require_permissions("stock.suppliers.create"))])
def create_supplier_endpoint(data: SupplierCreate, db: Session = Depends(get_db)):
    if db.query(Supplier).filter(Supplier.document == data.document).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supplier document already exists")
    s = Supplier(**data.dict())
    db.add(s)
    db.commit()
    db.refresh(s)
    return SupplierOut(**s.__dict__)


@router.get("/suppliers/{supplier_id}", response_model=SupplierOut)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return SupplierOut(**s.__dict__)


@router.put("/suppliers/{supplier_id}", response_model=SupplierOut, dependencies=[Depends(require_permissions("stock.suppliers.update"))])
def update_supplier_endpoint(supplier_id: int, data: SupplierUpdate, db: Session = Depends(get_db)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    for field, value in data.dict(exclude_none=True).items():
        setattr(s, field, value)
    db.add(s)
    db.commit()
    db.refresh(s)
    return SupplierOut(**s.__dict__)


# Veículos
@router.get("/vehicles", response_model=List[VehicleOut])
def list_vehicles(active: Optional[bool] = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Vehicle)
    if active is not None:
        q = q.filter(Vehicle.is_active == active)
    items = q.all()
    return [VehicleOut(**v.__dict__) for v in items]


@router.post("/vehicles", response_model=VehicleOut, dependencies=[Depends(require_permissions("stock.vehicles.create"))])
def create_vehicle_endpoint(data: VehicleCreate, db: Session = Depends(get_db)):
    v = create_vehicle(db, data)
    return VehicleOut(**v.__dict__)


# Kits
@router.get("/kits", response_model=List[KitOut])
def list_kits(db: Session = Depends(get_db)):
    items = db.query(Kit).all()
    return [KitOut(**k.__dict__) for k in items]


@router.post("/kits", response_model=KitOut, dependencies=[Depends(require_permissions("stock.kits.create"))])
def create_kit_endpoint(data: KitCreate, db: Session = Depends(get_db)):
    k = create_kit(db, data)
    return KitOut(**k.__dict__)


# Compras
@router.get("/purchases", response_model=List[PurchaseOut])
def list_purchases(db: Session = Depends(get_db)):
    items = db.query(Purchase).all()
    return [PurchaseOut(**p.__dict__) for p in items]


@router.post("/purchases", response_model=PurchaseOut, dependencies=[Depends(require_permissions("stock.purchases.create"))])
def create_purchase_endpoint(data: PurchaseCreate, db: Session = Depends(get_db)):
    p = create_purchase(db, data)
    return PurchaseOut(**p.__dict__)


@router.post("/purchases/items", dependencies=[Depends(require_permissions("stock.purchases.create"))])
def add_purchase_item_endpoint(data: PurchaseItemCreate, db: Session = Depends(get_db)):
    add_purchase_item(db, data)
    return {"ok": True}


# Transferências
@router.get("/transfers", response_model=List[TransferOut])
def list_transfers(db: Session = Depends(get_db)):
    items = db.query(Transfer).all()
    return [TransferOut(**t.__dict__) for t in items]


@router.post("/transfers", response_model=TransferOut, dependencies=[Depends(require_permissions("stock.transfers.create"))])
def create_transfer_endpoint(data: TransferCreate, db: Session = Depends(get_db)):
    t = create_transfer(db, data)
    return TransferOut(**t.__dict__)


@router.post("/transfers/items", dependencies=[Depends(require_permissions("stock.transfers.create"))])
def add_transfer_item_endpoint(data: TransferItemCreate, db: Session = Depends(get_db)):
    add_transfer_item(db, data)
    return {"ok": True}


@router.post("/kits/items", dependencies=[Depends(require_permissions("stock.kits.create"))])
def add_kit_item_endpoint(data: KitItemCreate, db: Session = Depends(get_db)):
    add_kit_item(db, data)
    return {"ok": True}


# Ajustes de estoque
@router.get("/adjustments", response_model=List[AdjustmentOut])
def list_adjustments(item_id: Optional[int] = None, warehouse_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(StockAdjustment)
    if item_id is not None:
        q = q.filter(StockAdjustment.item_id == item_id)
    if warehouse_id is not None:
        q = q.filter(StockAdjustment.warehouse_id == warehouse_id)
    items = q.order_by(StockAdjustment.created_at.desc()).limit(200).all()
    return [AdjustmentOut(**a.__dict__) for a in items]


@router.post("/adjustments", response_model=AdjustmentOut, dependencies=[Depends(require_permissions("stock.movements.create"))])
def create_adjustment_endpoint(data: AdjustmentCreate, db: Session = Depends(get_db)):
    try:
        adj = register_adjustment(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return AdjustmentOut(**adj.__dict__)


@router.post("/purchases/import-nfe", response_model=NFeImportOut, dependencies=[Depends(require_permissions("stock.purchases.create"))])
def import_nfe_endpoint(data: NFeImportRequest, db: Session = Depends(get_db)):
    p = import_nfe_purchase(db, data)
    return NFeImportOut(purchase_id=p.id, document_number=p.document_number, supplier_name=p.supplier_name, items_imported=int(p.total_value > 0))


# ===== COMODATO =====

@router.get("/comodatos", response_model=List[ComodatoOut])
def list_comodatos(
    client_id: Optional[int] = Query(default=None),
    contract_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista comodatos.
    """
    q = db.query(Comodato)

    if client_id is not None:
        q = q.filter(Comodato.client_id == client_id)
    if contract_id is not None:
        q = q.filter(Comodato.contract_id == contract_id)
    if status is not None:
        q = q.filter(Comodato.status == status)

    comodatos = q.order_by(Comodato.loan_date.desc()).all()
    return [ComodatoOut(**c.__dict__) for c in comodatos]


@router.post("/comodatos", response_model=ComodatoOut, dependencies=[Depends(require_permissions("stock.comodatos.create"))])
def create_comodato_endpoint(data: ComodatoCreate, db: Session = Depends(get_db)):
    """
    Cria comodato (empréstimo de equipamento).
    """
    try:
        comodato = create_comodato(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ComodatoOut(**comodato.__dict__)


@router.get("/comodatos/{comodato_id}", response_model=ComodatoOut)
def get_comodato(comodato_id: int, db: Session = Depends(get_db)):
    """
    Busca comodato por ID.
    """
    comodato = db.query(Comodato).filter(Comodato.id == comodato_id).first()
    if not comodato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comodato not found")

    return ComodatoOut(**comodato.__dict__)


@router.post("/comodatos/{comodato_id}/return", response_model=ComodatoOut, dependencies=[Depends(require_permissions("stock.comodatos.update"))])
def return_comodato_endpoint(
    comodato_id: int,
    data: ComodatoUpdate,
    db: Session = Depends(get_db)
):
    """
    Registra devolução de comodato.
    """
    comodato = db.query(Comodato).filter(Comodato.id == comodato_id).first()
    if not comodato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comodato not found")

    if not data.return_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="return_date is required")

    try:
        comodato = return_comodato(db, comodato, data.return_date, data.return_notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ComodatoOut(**comodato.__dict__)


@router.put("/comodatos/{comodato_id}/status", response_model=ComodatoOut, dependencies=[Depends(require_permissions("stock.comodatos.update"))])
def update_comodato_status_endpoint(
    comodato_id: int,
    data: ComodatoUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza status do comodato (lost, damaged, etc).
    """
    comodato = db.query(Comodato).filter(Comodato.id == comodato_id).first()
    if not comodato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comodato not found")

    if not data.status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status is required")

    try:
        comodato = update_comodato_status(db, comodato, data.status, data.return_notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ComodatoOut(**comodato.__dict__)


@router.get("/comodatos/client/{client_id}/active", response_model=List[ComodatoOut])
def get_client_active_comodatos(client_id: int, db: Session = Depends(get_db)):
    """
    Retorna comodatos ativos de um cliente.
    """
    comodatos = get_active_comodatos_by_client(db, client_id)
    return [ComodatoOut(**c.__dict__) for c in comodatos]
