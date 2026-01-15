"""
Arquivo: app/modules/administration/pops/routes.py

Responsabilidade:
Rotas REST para POPs.

Integrações:
- core.dependencies
- modules.administration.pops.service
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import POP
from .schemas import POPCreate, POPOut
from .service import create_pop


router = APIRouter()


@router.get("/", response_model=List[POPOut])
def list_pops(db: Session = Depends(get_db)):
    pops = db.query(POP).all()
    return [POPOut(id=p.id, name=p.name, city=p.city, address=p.address, latitude=p.latitude, longitude=p.longitude) for p in pops]


@router.post("/", response_model=POPOut, dependencies=[Depends(require_permissions("admin.pops.create"))])
def create_pop_endpoint(data: POPCreate, db: Session = Depends(get_db)):
    if db.query(POP).filter(POP.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="POP already exists")
    pop = create_pop(db, data)
    return POPOut(id=pop.id, name=pop.name, city=pop.city, address=pop.address, latitude=pop.latitude, longitude=pop.longitude)


@router.get("/{pop_id}", response_model=POPOut)
def get_pop(pop_id: int, db: Session = Depends(get_db)):
    pop = db.query(POP).filter(POP.id == pop_id).first()
    if not pop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="POP not found")
    return POPOut(id=pop.id, name=pop.name, city=pop.city, address=pop.address, latitude=pop.latitude, longitude=pop.longitude)

