from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_

from app.models.domain_models import RentalApplication, Property
from app.repositories.base_repository import AbstractRepository


class ApplicationRepository(AbstractRepository[RentalApplication]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> Optional[RentalApplication]:
        result = await self.db.execute(select(RentalApplication).where(RentalApplication.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[RentalApplication]:
        result = await self.db.execute(select(RentalApplication).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_for_tenant(self, tenant_id: int, status: Optional[str], page: int, page_size: int) -> Tuple[List[RentalApplication], int]:
        filters = [RentalApplication.tenant_id == tenant_id]
        if status:
            filters.append(RentalApplication.status == status)
        total = (await self.db.execute(select(func.count()).select_from(RentalApplication).where(and_(*filters)))).scalar_one()
        result = await self.db.execute(select(RentalApplication).where(and_(*filters)).order_by(RentalApplication.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_for_property(self, property_id: int, status: Optional[str], page: int, page_size: int) -> Tuple[List[RentalApplication], int]:
        filters = [RentalApplication.property_id == property_id]
        if status:
            filters.append(RentalApplication.status == status)
        total = (await self.db.execute(select(func.count()).select_from(RentalApplication).where(and_(*filters)))).scalar_one()
        result = await self.db.execute(select(RentalApplication).where(and_(*filters)).order_by(RentalApplication.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_for_landlord(
        self,
        landlord_id: int,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[RentalApplication], int]:
        """All applications across every property owned by the landlord (advanced search)."""
        filters = [Property.landlord_id == landlord_id]
        if status:
            filters.append(RentalApplication.status == status)
        if date_from:
            filters.append(RentalApplication.created_at >= date_from)
        if date_to:
            filters.append(RentalApplication.created_at <= date_to)

        base = select(RentalApplication).join(Property, Property.id == RentalApplication.property_id).where(and_(*filters))
        total = (await self.db.execute(
            select(func.count()).select_from(RentalApplication)
            .join(Property, Property.id == RentalApplication.property_id).where(and_(*filters))
        )).scalar_one()
        order = RentalApplication.created_at.asc() if sort_order == "asc" else RentalApplication.created_at.desc()
        result = await self.db.execute(base.order_by(order).offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def create(self, **kwargs) -> RentalApplication:
        app = RentalApplication(**kwargs)
        self.db.add(app)
        await self.db.flush()
        return app

    async def update(self, id: int, **kwargs) -> Optional[RentalApplication]:
        await self.db.execute(update(RentalApplication).where(RentalApplication.id == id).values(**kwargs))
        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(update(RentalApplication).where(RentalApplication.id == id).values(status="withdrawn"))
        return result.rowcount > 0
