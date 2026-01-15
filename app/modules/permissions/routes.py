"""
Arquivo: app/modules/permissions/routes.py

Responsabilidade:
Rotas REST para gestão de permissões.

Integrações:
- core.dependencies
- modules.permissions.models
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Permission
from .schemas import PermissionCreate, PermissionOut


router = APIRouter()


@router.get("/", response_model=List[PermissionOut])
def list_permissions(db: Session = Depends(get_db)):
    perms = db.query(Permission).all()
    return [PermissionOut(id=p.id, code=p.code, description=p.description) for p in perms]


@router.post("/", response_model=PermissionOut, dependencies=[Depends(require_permissions("permissions.create"))])
def create_permission_endpoint(data: PermissionCreate, db: Session = Depends(get_db)):
    if db.query(Permission).filter(Permission.code == data.code).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exists")
    p = Permission(code=data.code, description=data.description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return PermissionOut(id=p.id, code=p.code, description=p.description)

