from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user_models import User
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService
from app.schemas.notification_schemas import NotificationOut

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))


@router.get("", response_model=List[NotificationOut])
async def list_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    svc: NotificationService = Depends(_svc),
):
    return await svc.get_for_user(current_user.id, unread_only)


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: NotificationService = Depends(_svc),
):
    await svc.mark_read(notification_id, current_user.id)
    await db.commit()
