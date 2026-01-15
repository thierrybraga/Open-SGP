"""
Arquivo: app/modules/roles/service.py

Responsabilidade:
Regras de negócio para criação e gestão de roles.

Integrações:
- modules.roles.models
- modules.permissions.models
"""

from sqlalchemy.orm import Session

from .models import Role
from ..permissions.models import Permission
from .schemas import RoleCreate


def create_role(db: Session, data: RoleCreate) -> Role:
    role = Role(name=data.name)
    if data.permissions:
        perms = db.query(Permission).filter(Permission.code.in_(data.permissions)).all()
        role.permissions = perms
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

