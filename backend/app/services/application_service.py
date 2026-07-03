from fastapi import HTTPException, status

from app.repositories.application_repository import ApplicationRepository
from app.services.notification_service import NotificationService
from app.models.user_models import User
from app.schemas.application_schemas import ApplicationCreateRequest, ApplicationStatusUpdate


class ApplicationService:
    def __init__(self, repo: ApplicationRepository, notification_svc: NotificationService):
        self.repo = repo
        self.notification_svc = notification_svc

    async def create(self, data: ApplicationCreateRequest, current_user: User):
        return await self.repo.create(
            property_id=data.property_id,
            tenant_id=current_user.id,
            message=data.message,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

    async def get_for_tenant(self, user: User, status_filter, page, page_size):
        return await self.repo.get_for_tenant(user.id, status_filter, page, page_size)

    async def get_for_property(self, property_id: int, status_filter, page, page_size):
        return await self.repo.get_for_property(property_id, status_filter, page, page_size)

    async def get_for_landlord(self, user: User, status_filter, date_from, date_to, sort_order, page, page_size):
        return await self.repo.get_for_landlord(
            user.id, status_filter, date_from, date_to, sort_order, page, page_size
        )

    async def update_status(self, application_id: int, data: ApplicationStatusUpdate, current_user: User):
        app = await self.repo.get_by_id(application_id)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        updated = await self.repo.update(application_id, status=data.status, updated_by=current_user.id)

        if data.status in ("approved", "rejected"):
            await self.notification_svc.notify(
                user_id=app.tenant_id,
                type="application_update",
                title=f"Application {data.status.capitalize()}",
                message=f"Your rental application has been {data.status}.",
            )

        return updated
