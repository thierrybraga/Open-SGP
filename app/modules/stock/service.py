"""
Arquivo: app/modules/stock/service.py

Responsabilidade:
Regras de negócio de Estoque: CRUD de itens e almoxarifados, registro de
movimentos e cálculo de saldo.

Integrações:
- modules.stock.models
"""

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from .models import Warehouse, StockItem, StockMovement
from .schemas import (
    WarehouseCreate,
    WarehouseUpdate,
    StockItemCreate,
    StockItemUpdate,
    MovementCreate,
    StockBalance,
)
from .models import StockCategory, Manufacturer, Vehicle, Kit, KitItem, Purchase, PurchaseItem, Transfer, TransferItem, StockAdjustment
from .schemas import (
    CategoryCreate,
    ManufacturerCreate,
    VehicleCreate,
    KitCreate,
    KitItemCreate,
    PurchaseCreate,
    PurchaseItemCreate,
    TransferCreate,
    TransferItemCreate,
    AdjustmentCreate,
    NFeImportRequest,
)


def create_warehouse(db: Session, data: WarehouseCreate) -> Warehouse:
    w = Warehouse(**data.dict())
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def update_warehouse(db: Session, w: Warehouse, data: WarehouseUpdate) -> Warehouse:
    for field, value in data.dict(exclude_none=True).items():
        setattr(w, field, value)
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def create_item(db: Session, data: StockItemCreate) -> StockItem:
    i = StockItem(**data.dict())
    db.add(i)
    db.commit()
    db.refresh(i)
    return i


def update_item(db: Session, i: StockItem, data: StockItemUpdate) -> StockItem:
    for field, value in data.dict(exclude_none=True).items():
        setattr(i, field, value)
    db.add(i)
    db.commit()
    db.refresh(i)
    return i


def register_movement(db: Session, data: MovementCreate) -> StockMovement:
    total_value = None
    if data.unit_cost is not None:
        total_value = data.unit_cost * data.quantity
    if data.type == "out":
        bal = get_balance(db, item_id=data.item_id, warehouse_id=data.warehouse_id)
        if data.quantity > bal.quantity:
            raise ValueError("Insufficient stock for outgoing movement")
    m = StockMovement(
        item_id=data.item_id,
        warehouse_id=data.warehouse_id,
        type=data.type,
        quantity=data.quantity,
        unit_cost=data.unit_cost,
        total_value=total_value,
        note=data.note,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def get_balance(db: Session, item_id: int, warehouse_id: int | None = None) -> StockBalance:
    q = db.query(
        func.sum(
            case((StockMovement.type == "in", StockMovement.quantity), else_=0.0)
        ).label("in_qty"),
        func.sum(
            case((StockMovement.type == "out", StockMovement.quantity), else_=0.0)
        ).label("out_qty"),
    ).filter(StockMovement.item_id == item_id)
    if warehouse_id is not None:
        q = q.filter(StockMovement.warehouse_id == warehouse_id)

    in_qty, out_qty = q.first()
    in_qty = float(in_qty or 0.0)
    out_qty = float(out_qty or 0.0)
    quantity = in_qty - out_qty
    return StockBalance(item_id=item_id, warehouse_id=warehouse_id, quantity=quantity)


def create_category(db: Session, data: CategoryCreate) -> StockCategory:
    c = StockCategory(**data.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def create_manufacturer(db: Session, data: ManufacturerCreate) -> Manufacturer:
    m = Manufacturer(**data.dict())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def create_vehicle(db: Session, data: VehicleCreate) -> Vehicle:
    v = Vehicle(**data.dict())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def create_kit(db: Session, data: KitCreate) -> Kit:
    k = Kit(**data.dict())
    db.add(k)
    db.commit()
    db.refresh(k)
    return k


def create_purchase(db: Session, data: PurchaseCreate) -> Purchase:
    p = Purchase(**data.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def add_purchase_item(db: Session, data: PurchaseItemCreate) -> PurchaseItem:
    pi = PurchaseItem(**data.dict())
    db.add(pi)
    # Atualiza total
    db.flush()
    purchase = db.query(Purchase).filter(Purchase.id == pi.purchase_id).first()
    total = db.query(func.sum(PurchaseItem.unit_cost * PurchaseItem.quantity)).filter(PurchaseItem.purchase_id == pi.purchase_id).scalar() or 0.0
    purchase.total_value = float(total)
    db.add(purchase)
    db.commit()
    db.refresh(pi)
    # Movimento de entrada automático
    m = StockMovement(
        item_id=pi.item_id,
        warehouse_id=pi.warehouse_id,
        type="in",
        quantity=pi.quantity,
        unit_cost=pi.unit_cost,
        total_value=pi.unit_cost * pi.quantity,
        note=f"Compra {purchase.document_number}",
    )
    db.add(m)
    db.commit()
    return pi


def create_transfer(db: Session, data: TransferCreate) -> Transfer:
    t = Transfer(**data.dict())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def add_transfer_item(db: Session, data: TransferItemCreate) -> TransferItem:
    ti = TransferItem(**data.dict())
    db.add(ti)
    db.flush()
    transfer = db.query(Transfer).filter(Transfer.id == ti.transfer_id).first()
    # saída do almoxarifado origem
    m_out = StockMovement(
        item_id=ti.item_id,
        warehouse_id=transfer.from_warehouse_id,
        type="out",
        quantity=ti.quantity,
        unit_cost=None,
        total_value=None,
        note=f"Transferência {transfer.id} saída",
    )
    db.add(m_out)
    # entrada no almoxarifado destino
    m_in = StockMovement(
        item_id=ti.item_id,
        warehouse_id=transfer.to_warehouse_id,
        type="in",
        quantity=ti.quantity,
        unit_cost=None,
        total_value=None,
        note=f"Transferência {transfer.id} entrada",
    )
    db.add(m_in)
    db.commit()
    db.refresh(ti)
    return ti


def add_kit_item(db: Session, data: KitItemCreate) -> KitItem:
    ki = KitItem(**data.dict())
    db.add(ki)
    db.commit()
    db.refresh(ki)
    return ki


def register_adjustment(db: Session, data: AdjustmentCreate) -> StockAdjustment:
    if data.type not in ("increase", "decrease"):
        raise ValueError("Invalid adjustment type")
    if data.quantity <= 0:
        raise ValueError("Quantity must be > 0")
    adj = StockAdjustment(**data.dict())
    db.add(adj)
    db.commit()
    db.refresh(adj)
    # reflect into movement
    move_type = "in" if data.type == "increase" else "out"
    m = StockMovement(
        item_id=data.item_id,
        warehouse_id=data.warehouse_id,
        type=move_type,
        quantity=data.quantity,
        unit_cost=None,
        total_value=None,
        note=f"Ajuste: {data.reason} {data.ref_document or ''}".strip(),
    )
    db.add(m)
    db.commit()
    return adj


def import_nfe_purchase(db: Session, req: NFeImportRequest) -> Purchase:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(req.xml_content)

    def _text(el):
        return el.text.strip() if el is not None and el.text else ""

    def find(path: str):
        return root.find(path) or root.find(path.replace("*", ""))

    # Namespaced-friendly queries
    emit_name = root.find('.//{*}emit/{*}xNome')
    supplier_name = _text(emit_name) or "Fornecedor"
    ide_nnf = root.find('.//{*}ide/{*}nNF')
    doc_number = _text(ide_nnf) or f"NF-{int(func.random()*100000)}"

    p = Purchase(supplier_name=supplier_name, document_number=doc_number, total_value=0.0)
    db.add(p)
    db.commit()
    db.refresh(p)

    total_value = 0.0
    for det in root.findall('.//{*}det'):
        prod = det.find('.//{*}prod')
        if prod is None:
            prod = det.find('prod')
        cProd = _text(prod.find('{*}cProd')) if prod is not None else ""
        xProd = _text(prod.find('{*}xProd')) if prod is not None else "Item"
        qCom = _text(prod.find('{*}qCom')) if prod is not None else "0"
        vUnCom = _text(prod.find('{*}vUnCom')) if prod is not None else "0"
        uCom = _text(prod.find('{*}uCom')) if prod is not None else "UN"

        try:
            qty = float(qCom.replace(',', '.'))
        except Exception:
            qty = 0.0
        try:
            unit_cost = float(vUnCom.replace(',', '.'))
        except Exception:
            unit_cost = 0.0

        item = db.query(StockItem).filter(StockItem.code == cProd).first()
        if not item and req.create_missing_items:
            item = StockItem(name=xProd or cProd or "Item", code=cProd or f"AUTO-{p.id}-{det.attrib.get('nItem','')}", unit=uCom or "UN", min_qty=0.0, is_active=True)
            db.add(item)
            db.commit()
            db.refresh(item)
        if not item:
            continue

        pi = PurchaseItem(purchase_id=p.id, item_id=item.id, quantity=qty, unit_cost=unit_cost, warehouse_id=req.warehouse_id)
        db.add(pi)
        db.commit()
        total_value += unit_cost * qty

        # movimento automático já é gerado por add_purchase_item; aqui refletimos manualmente para importação direta
        m = StockMovement(
            item_id=item.id,
            warehouse_id=req.warehouse_id,
            type="in",
            quantity=qty,
            unit_cost=unit_cost,
            total_value=unit_cost * qty,
            note=f"Importação NFe {doc_number}",
        )
        db.add(m)
        db.commit()

    p.total_value = float(total_value)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ===== COMODATO =====

def create_comodato(db: Session, data) -> "Comodato":
    """
    Cria um comodato (empréstimo de equipamento).
    Registra movimentação de saída no estoque.
    """
    from .models import Comodato, StockMovement

    # Criar comodato
    comodato = Comodato(**data.dict())
    comodato.status = "active"
    db.add(comodato)
    db.flush()

    # Registrar movimentação de saída no estoque
    movement = StockMovement(
        item_id=data.item_id,
        warehouse_id=data.warehouse_id,
        type="out",
        quantity=data.quantity,
        note=f"Comodato #{comodato.id} - Cliente #{data.client_id}"
    )
    db.add(movement)

    db.commit()
    db.refresh(comodato)
    return comodato


def return_comodato(db: Session, comodato: "Comodato", return_date: str, return_notes: str = None) -> "Comodato":
    """
    Registra devolução de comodato.
    Registra movimentação de entrada no estoque.
    """
    from .models import StockMovement

    if comodato.status != "active":
        raise ValueError("Comodato is not active")

    # Atualizar comodato
    comodato.status = "returned"
    comodato.return_date = return_date
    comodato.return_notes = return_notes
    db.add(comodato)
    db.flush()

    # Registrar movimentação de entrada no estoque
    movement = StockMovement(
        item_id=comodato.item_id,
        warehouse_id=comodato.warehouse_id,
        type="in",
        quantity=comodato.quantity,
        note=f"Devolução Comodato #{comodato.id}"
    )
    db.add(movement)

    db.commit()
    db.refresh(comodato)
    return comodato


def update_comodato_status(db: Session, comodato: "Comodato", status: str, notes: str = None) -> "Comodato":
    """
    Atualiza status do comodato (lost, damaged, etc).
    Para status 'lost' ou 'damaged', NÃO registra devolução de estoque.
    """
    if status not in ["active", "returned", "lost", "damaged"]:
        raise ValueError("Invalid status")

    comodato.status = status
    if notes:
        comodato.return_notes = notes

    db.add(comodato)
    db.commit()
    db.refresh(comodato)
    return comodato


def get_active_comodatos_by_client(db: Session, client_id: int) -> list:
    """
    Retorna comodatos ativos de um cliente.
    """
    from .models import Comodato

    return db.query(Comodato).filter(
        Comodato.client_id == client_id,
        Comodato.status == "active"
    ).all()
