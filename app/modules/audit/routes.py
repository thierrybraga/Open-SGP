"""
Arquivo: app/modules/audit/routes.py

Responsabilidade:
Endpoints para consulta de auditoria.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_permissions
from app.modules.audit.service import AuditService
from app.modules.audit.models import AuditLog
from typing import List
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/api/audit", tags=["Audit"])


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
def get_entity_history(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _: None = Depends(require_permissions(["audit.view"]))
):
    """Retorna histórico de mudanças de uma entidade"""
    return AuditService.get_entity_history(db, entity_type, entity_id, limit)


@router.get("/user/{user_id}", response_model=List[AuditLogResponse])
def get_user_actions(
    user_id: int,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _: None = Depends(require_permissions(["audit.view"]))
):
    """Retorna ações de um usuário"""
    return AuditService.get_user_actions(db, user_id, limit)
