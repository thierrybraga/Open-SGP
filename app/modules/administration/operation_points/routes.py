"""
Arquivo: app/modules/administration/operation_points/routes.py

Responsabilidade:
Rotas REST para Pontos de Operação.

Integrações:
- core.dependencies
- modules.administration.operation_points.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import OperationPoint
from .schemas import OperationPointCreate, OperationPointUpdate, OperationPointOut
from .service import (
    create_operation_point,
    update_operation_point,
    get_active_operation_points,
    get_operation_points_by_city,
    get_operation_points_by_type
)


router = APIRouter()


@router.get("/", response_model=List[OperationPointOut])
def list_operation_points(
    city: Optional[str] = Query(default=None),
    point_type: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lista pontos de operação com filtros opcionais.
    """
    q = db.query(OperationPoint)

    if city:
        q = q.filter(OperationPoint.city.ilike(f"%{city}%"))
    if point_type:
        q = q.filter(OperationPoint.point_type == point_type)
    if is_active is not None:
        q = q.filter(OperationPoint.is_active == is_active)

    points = q.order_by(OperationPoint.name).all()
    return [OperationPointOut(**p.__dict__) for p in points]


@router.post("/", response_model=OperationPointOut, dependencies=[Depends(require_permissions("administration.operation_points.create"))])
def create_operation_point_endpoint(data: OperationPointCreate, db: Session = Depends(get_db)):
    """
    Cria novo ponto de operação.
    """
    try:
        point = create_operation_point(db, data)
        return OperationPointOut(**point.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{point_id}", response_model=OperationPointOut)
def get_operation_point(point_id: int, db: Session = Depends(get_db)):
    """
    Busca ponto de operação por ID.
    """
    point = db.query(OperationPoint).filter(OperationPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation point not found")

    return OperationPointOut(**point.__dict__)


@router.put("/{point_id}", response_model=OperationPointOut, dependencies=[Depends(require_permissions("administration.operation_points.update"))])
def update_operation_point_endpoint(
    point_id: int,
    data: OperationPointUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza ponto de operação.
    """
    point = db.query(OperationPoint).filter(OperationPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation point not found")

    point = update_operation_point(db, point, data)
    return OperationPointOut(**point.__dict__)


@router.delete("/{point_id}", dependencies=[Depends(require_permissions("administration.operation_points.delete"))])
def delete_operation_point(point_id: int, db: Session = Depends(get_db)):
    """
    Remove ponto de operação.
    """
    point = db.query(OperationPoint).filter(OperationPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation point not found")

    db.delete(point)
    db.commit()

    return {"message": "Operation point deleted successfully"}


@router.get("/active/list", response_model=List[OperationPointOut])
def list_active_operation_points(db: Session = Depends(get_db)):
    """
    Lista pontos de operação ativos.
    """
    points = get_active_operation_points(db)
    return [OperationPointOut(**p.__dict__) for p in points]


@router.get("/by-type/{point_type}", response_model=List[OperationPointOut])
def list_by_type(point_type: str, db: Session = Depends(get_db)):
    """
    Lista pontos de operação por tipo.
    """
    points = get_operation_points_by_type(db, point_type)
    return [OperationPointOut(**p.__dict__) for p in points]
