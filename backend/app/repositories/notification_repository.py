from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.audit_models import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, type: str, title: str, message: str) -> Notification:
        n = Notification(user_id=user_id, type=type, title=title, message=message)
        self.db.add(n)
        await self.db.flush()
        return n

    async def get_for_user(self, user_id: int, unread_only: bool = False) -> List[Notification]:
        q = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.is_read == False)  # noqa: E712
        result = await self.db.execute(q.order_by(Notification.created_at.desc()).limit(50))
        return list(result.scalars().all())

    async def mark_read(self, notification_id: int, user_id: int) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True)
        )
