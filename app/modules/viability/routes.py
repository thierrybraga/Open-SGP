"""
Arquivo: app/modules/viability/routes.py

Responsabilidade:
Rotas REST para Viabilidade Técnica.

Integrações:
- core.dependencies
- modules.viability.service
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions, get_current_user
from .models import Viability
from .schemas import ViabilityCreate, ViabilityUpdate, ViabilityAnalyze, ViabilityOut
from .service import create_viability, update_viability, analyze_viability, get_pending_viabilities, check_expired_viabilities


router = APIRouter()


@router.get("/", response_model=List[ViabilityOut])
def list_viabilities(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    client_id: Optional[int] = Query(default=None),
    plan_id: Optional[int] = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lista viabilidades com filtros.
    """
    q = db.query(Viability)

    if status_filter:
        q = q.filter(Viability.status == status_filter)
    if client_id:
        q = q.filter(Viability.client_id == client_id)
    if plan_id:
        q = q.filter(Viability.plan_id == plan_id)

    items = q.order_by(Viability.created_at.desc()).offset(skip).limit(limit).all()
    return [ViabilityOut(**v.__dict__) for v in items]


@router.post("/", response_model=ViabilityOut, dependencies=[Depends(require_permissions("viability.create"))])
def create_viability_endpoint(
    data: ViabilityCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cria nova análise de viabilidade técnica.
    """
    try:
        v = create_viability(db, data, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ViabilityOut(**v.__dict__)


@router.get("/pending", response_model=List[ViabilityOut])
def list_pending_viabilities_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lista viabilidades pendentes de análise (não expiradas).
    """
    items = get_pending_viabilities(db, skip, limit)
    return [ViabilityOut(**v.__dict__) for v in items]


@router.get("/{viability_id}", response_model=ViabilityOut)
def get_viability(viability_id: int, db: Session = Depends(get_db)):
    """
    Busca viabilidade por ID.
    """
    v = db.query(Viability).filter(Viability.id == viability_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viability not found")

    return ViabilityOut(**v.__dict__)


@router.put("/{viability_id}", response_model=ViabilityOut, dependencies=[Depends(require_permissions("viability.update"))])
def update_viability_endpoint(
    viability_id: int,
    data: ViabilityUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de uma viabilidade.
    """
    v = db.query(Viability).filter(Viability.id == viability_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viability not found")

    v = update_viability(db, v, data)
    return ViabilityOut(**v.__dict__)


@router.post("/{viability_id}/analyze", response_model=ViabilityOut, dependencies=[Depends(require_permissions("viability.analyze"))])
def analyze_viability_endpoint(
    viability_id: int,
    data: ViabilityAnalyze,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Analisa e aprova/rejeita uma viabilidade técnica.
    """
    v = db.query(Viability).filter(Viability.id == viability_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viability not found")

    try:
        v = analyze_viability(db, v, data, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ViabilityOut(**v.__dict__)


@router.post("/check-expired", dependencies=[Depends(require_permissions("viability.admin"))])
def check_expired_endpoint(db: Session = Depends(get_db)):
    """
    Verifica e marca viabilidades expiradas.
    """
    count = check_expired_viabilities(db)
    return {"expired_count": count, "message": f"{count} viabilities marked as expired"}
