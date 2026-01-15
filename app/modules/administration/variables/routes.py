"""
Arquivo: app/modules/administration/variables/routes.py

Responsabilidade:
Rotas REST para variáveis de sistema.

Integrações:
- core.dependencies
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.dependencies import get_db, require_permissions
from .models import SystemVariable
from .schemas import VariableCreate, VariableOut


router = APIRouter()


@router.get("/", response_model=List[VariableOut])
def list_variables(db: Session = Depends(get_db)):
    vars_ = db.query(SystemVariable).all()
    return [VariableOut(id=v.id, key=v.key, value=v.value, description=v.description) for v in vars_]


@router.post("/", response_model=VariableOut, dependencies=[Depends(require_permissions("admin.variables.create"))])
def create_variable_endpoint(data: VariableCreate, db: Session = Depends(get_db)):
    if db.query(SystemVariable).filter(SystemVariable.key == data.key).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Variable already exists")
    v = SystemVariable(key=data.key, value=data.value, description=data.description)
    db.add(v)
    db.commit()
    db.refresh(v)
    return VariableOut(id=v.id, key=v.key, value=v.value, description=v.description)

