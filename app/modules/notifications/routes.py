"""
Arquivo: app/modules/notifications/routes.py

Responsabilidade:
Rotas da API de Notificações.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...modules.auth.routes import get_current_user
from ...modules.users.models import User
from .schemas import NotificationOut, NotificationCreate
from .service import (
    get_user_notifications,
    create_notification,
    mark_as_read,
    mark_all_as_read,
    get_unread_count
)

router = APIRouter()


@router.get("/", response_model=List[NotificationOut])
def list_notifications(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_notifications(db, user.id, limit)


@router.get("/unread-count")
def count_unread(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {"count": get_unread_count(db, user.id)}


@router.post("/{notification_id}/read")
def read_notification(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = mark_as_read(db, notification_id, user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}


@router.post("/read-all")
def read_all_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    mark_all_as_read(db, user.id)
    return {"status": "success"}


# Internal use or admin only - for testing purposes mostly
@router.post("/", response_model=NotificationOut)
def create_notification_endpoint(
    data: NotificationCreate,
    user: User = Depends(get_current_user), # In real scenario, verify admin permissions
    db: Session = Depends(get_db)
):
    return create_notification(db, data)
