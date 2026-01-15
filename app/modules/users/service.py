"""
Arquivo: app/modules/users/service.py

Responsabilidade:
Regras de negócio para criação e gestão de usuários.

Integrações:
- modules.users.models
- core.security
"""

from sqlalchemy.orm import Session

from .models import User
from ..roles.models import Role
from .schemas import UserCreate, UserUpdate
from ...core.security import hash_password


def create_user(db: Session, data: UserCreate) -> User:
    user = User(username=data.username, email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    if data.email is not None:
        user.email = data.email
    if data.is_active is not None:
        user.is_active = data.is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_user_roles(db: Session, user: User, role_names: list[str]) -> User:
    roles = db.query(Role).filter(Role.name.in_(role_names)).all()
    user.roles = roles
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
