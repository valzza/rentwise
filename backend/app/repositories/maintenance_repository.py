from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_

from app.models.domain_models import MaintenanceRequest, Property
from app.repositories.base_repository import AbstractRepository


class MaintenanceRepository(AbstractRepository[MaintenanceRequest]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> Optional[MaintenanceRequest]:
        result = await self.db.execute(select(MaintenanceRequest).where(MaintenanceRequest.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[MaintenanceRequest]:
        result = await self.db.execute(select(MaintenanceRequest).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_for_property(self, property_id: int) -> List[MaintenanceRequest]:
        result = await self.db.execute(select(MaintenanceRequest).where(MaintenanceRequest.property_id == property_id).order_by(MaintenanceRequest.created_at.desc()))
        return list(result.scalars().all())

    async def get_for_tenant(self, tenant_id: int) -> List[MaintenanceRequest]:
        result = await self.db.execute(select(MaintenanceRequest).where(MaintenanceRequest.tenant_id == tenant_id).order_by(MaintenanceRequest.created_at.desc()))
        return list(result.scalars().all())

    async def search_for_landlord(
        self, landlord_id: int, status: Optional[str] = None, priority: Optional[str] = None,
        property_id: Optional[int] = None,
    ) -> List[MaintenanceRequest]:
        """All maintenance requests across the landlord's properties (advanced filters)."""
        filters = [Property.landlord_id == landlord_id]
        if status:
            filters.append(MaintenanceRequest.status == status)
        if priority:
            filters.append(MaintenanceRequest.priority == priority)
        if property_id:
            filters.append(MaintenanceRequest.property_id == property_id)
        result = await self.db.execute(
            select(MaintenanceRequest)
            .join(Property, Property.id == MaintenanceRequest.property_id)
            .where(and_(*filters))
            .order_by(MaintenanceRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> MaintenanceRequest:
        req = MaintenanceRequest(**kwargs)
        self.db.add(req)
        await self.db.flush()
        return req

    async def update(self, id: int, **kwargs) -> Optional[MaintenanceRequest]:
        await self.db.execute(update(MaintenanceRequest).where(MaintenanceRequest.id == id).values(**kwargs))
        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(update(MaintenanceRequest).where(MaintenanceRequest.id == id).values(status="closed"))
        return result.rowcount > 0
