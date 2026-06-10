from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def notify(self, user_id: int, type: str, title: str, message: str) -> None:
        """Create a DB notification and emit it live via Socket.IO."""
        await self.repo.create(user_id=user_id, type=type, title=title, message=message)

        # Emit real-time event — import here to avoid circular import at module level
        try:
            from app.websockets.socket_manager import emit_notification
            await emit_notification(user_id, {"type": type, "title": title, "message": message})
        except Exception:
            pass  # Socket.IO may not be connected in test environments

    async def get_for_user(self, user_id: int, unread_only: bool = False):
        return await self.repo.get_for_user(user_id, unread_only)

    async def mark_read(self, notification_id: int, user_id: int) -> None:
        await self.repo.mark_read(notification_id, user_id)
