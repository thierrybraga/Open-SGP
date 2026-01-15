"""
Arquivo: app/modules/users/routes.py

Responsabilidade:
Rotas REST para gestão de usuários.

Integrações:
- core.dependencies
- modules.users.service
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, require_permissions
from .models import User
from .schemas import UserCreate, UserUpdate, UserOut
from .service import create_user, update_user, set_user_roles
from ..roles.models import Role


router = APIRouter()


@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserOut(id=u.id, username=u.username, email=u.email, is_active=u.is_active, roles=[r.name for r in u.roles]) for u in users]


@router.post("/", response_model=UserOut, dependencies=[Depends(require_permissions("users.create"))])
def create_user_endpoint(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    user = create_user(db, data)
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active, roles=[r.name for r in user.roles])


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_permissions("users.update"))])
def update_user_endpoint(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = update_user(db, user, data)
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active, roles=[r.name for r in user.roles])


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active, roles=[r.name for r in user.roles])


@router.post("/{user_id}/roles", response_model=UserOut, dependencies=[Depends(require_permissions("users.roles.assign"))])
def assign_user_roles(user_id: int, role_names: List[str], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Valida roles existentes
    existing = {r.name for r in db.query(Role).filter(Role.name.in_(role_names)).all()}
    if not existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid roles provided")
    user = set_user_roles(db, user, list(existing))
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active, roles=[r.name for r in user.roles])
