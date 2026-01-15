"""
Arquivo: app/modules/roles/routes.py

Responsabilidade:
Rotas REST para gestão de roles.

Integrações:
- core.dependencies
- modules.roles.service
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import Role
from .schemas import RoleCreate, RoleOut
from .service import create_role


router = APIRouter()


@router.get("/", response_model=List[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return [RoleOut(id=r.id, name=r.name, permissions=[p.code for p in r.permissions]) for r in roles]


@router.post("/", response_model=RoleOut, dependencies=[Depends(require_permissions("roles.create"))])
def create_role_endpoint(data: RoleCreate, db: Session = Depends(get_db)):
    if db.query(Role).filter(Role.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")
    role = create_role(db, data)
    return RoleOut(id=role.id, name=role.name, permissions=[p.code for p in role.permissions])

