"""
Arquivo: app/modules/administration/operation_points/service.py

Responsabilidade:
Lógica de negócio para Pontos de Operação.
"""

from sqlalchemy.orm import Session
from .models import OperationPoint
from .schemas import OperationPointCreate, OperationPointUpdate


def create_operation_point(db: Session, data: OperationPointCreate) -> OperationPoint:
    """Cria novo ponto de operação."""
    # Verificar se código já existe
    existing = db.query(OperationPoint).filter(OperationPoint.code == data.code).first()
    if existing:
        raise ValueError(f"Operation point with code '{data.code}' already exists")

    point = OperationPoint(**data.dict())
    db.add(point)
    db.commit()
    db.refresh(point)
    return point


def update_operation_point(db: Session, point: OperationPoint, data: OperationPointUpdate) -> OperationPoint:
    """Atualiza ponto de operação."""
    for field, value in data.dict(exclude_none=True).items():
        setattr(point, field, value)

    db.add(point)
    db.commit()
    db.refresh(point)
    return point


def get_active_operation_points(db: Session) -> list[OperationPoint]:
    """Retorna pontos de operação ativos."""
    return db.query(OperationPoint).filter(OperationPoint.is_active == True).all()


def get_operation_points_by_city(db: Session, city: str) -> list[OperationPoint]:
    """Retorna pontos de operação de uma cidade."""
    return db.query(OperationPoint).filter(
        OperationPoint.city.ilike(f"%{city}%"),
        OperationPoint.is_active == True
    ).all()


def get_operation_points_by_type(db: Session, point_type: str) -> list[OperationPoint]:
    """Retorna pontos de operação de um tipo."""
    return db.query(OperationPoint).filter(
        OperationPoint.point_type == point_type,
        OperationPoint.is_active == True
    ).all()
