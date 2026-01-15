"""
Arquivo: app/modules/administration/nas/routes.py

Responsabilidade:
Rotas REST para NAS.

Integrações:
- core.dependencies
- modules.administration.nas.service
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import NAS
from .schemas import NASCreate, NASOut
from .service import create_nas


router = APIRouter()


@router.get("/", response_model=List[NASOut])
def list_nas(db: Session = Depends(get_db)):
    devices = db.query(NAS).all()
    return [NASOut(id=n.id, name=n.name, ip_address=n.ip_address, secret=n.secret, vendor=n.vendor, pop_id=n.pop_id) for n in devices]


@router.post("/", response_model=NASOut, dependencies=[Depends(require_permissions("admin.nas.create"))])
def create_nas_endpoint(data: NASCreate, db: Session = Depends(get_db)):
    if db.query(NAS).filter(NAS.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="NAS already exists")
    nas = create_nas(db, data)
    return NASOut(id=nas.id, name=nas.name, ip_address=nas.ip_address, secret=nas.secret, vendor=nas.vendor, pop_id=nas.pop_id)


@router.get("/{nas_id}", response_model=NASOut)
def get_nas(nas_id: int, db: Session = Depends(get_db)):
    nas = db.query(NAS).filter(NAS.id == nas_id).first()
    if not nas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NAS not found")
    return NASOut(id=nas.id, name=nas.name, ip_address=nas.ip_address, secret=nas.secret, vendor=nas.vendor, pop_id=nas.pop_id)

