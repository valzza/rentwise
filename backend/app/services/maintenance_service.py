from typing import List, Optional
from fastapi import HTTPException, status

from app.repositories.maintenance_repository import MaintenanceRepository
from app.services.notification_service import NotificationService
from app.models.user_models import User
from app.schemas.maintenance_schemas import MaintenanceCreateRequest, MaintenanceStatusUpdate


class MaintenanceService:
    def __init__(self, repo: MaintenanceRepository, notification_svc: NotificationService):
        self.repo = repo
        self.notification_svc = notification_svc

    async def create(self, data: MaintenanceCreateRequest, current_user: User):
        return await self.repo.create(
            property_id=data.property_id,
            tenant_id=current_user.id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

    async def list_for_tenant(self, current_user: User):
        return await self.repo.get_for_tenant(current_user.id)

    async def search_for_landlord(
        self, current_user: User, status_filter: Optional[str],
        priority: Optional[str], property_id: Optional[int],
    ) -> List:
        return await self.repo.search_for_landlord(current_user.id, status_filter, priority, property_id)

    async def update_status(self, request_id: int, data: MaintenanceStatusUpdate, current_user: User):
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")

        updates = data.model_dump(exclude_none=True)
        updates["updated_by"] = current_user.id
        updated = await self.repo.update(request_id, **updates)

        await self.notification_svc.notify(
            user_id=req.tenant_id,
            type="maintenance_update",
            title=f"Maintenance {data.status.replace('_', ' ').capitalize()}",
            message=f"Your maintenance request '{req.title}' is now {data.status}.",
        )
        return updated