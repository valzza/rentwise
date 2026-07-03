from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_

from app.models.domain_models import ViewingBooking
from app.repositories.base_repository import AbstractRepository


class BookingRepository(AbstractRepository[ViewingBooking]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> Optional[ViewingBooking]:
        result = await self.db.execute(select(ViewingBooking).where(ViewingBooking.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[ViewingBooking]:
        result = await self.db.execute(select(ViewingBooking).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_for_tenant(
        self, tenant_id: int, status: Optional[str], page: int, page_size: int,
        date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
        sort_order: str = "desc",
    ) -> Tuple[List[ViewingBooking], int]:
        filters = [ViewingBooking.tenant_id == tenant_id]
        if status:
            filters.append(ViewingBooking.status == status)
        if date_from:
            filters.append(ViewingBooking.scheduled_at >= date_from)
        if date_to:
            filters.append(ViewingBooking.scheduled_at <= date_to)
        total = (await self.db.execute(select(func.count()).select_from(ViewingBooking).where(and_(*filters)))).scalar_one()
        order = ViewingBooking.scheduled_at.asc() if sort_order == "asc" else ViewingBooking.scheduled_at.desc()
        result = await self.db.execute(
            select(ViewingBooking).where(and_(*filters))
            .order_by(order)
            .offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_for_landlord(
        self, landlord_id: int, status: Optional[str], page: int, page_size: int,
        date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
        sort_order: str = "desc",
    ) -> Tuple[List[ViewingBooking], int]:
        from app.models.domain_models import Property
        filters = [Property.landlord_id == landlord_id]
        if status:
            filters.append(ViewingBooking.status == status)
        if date_from:
            filters.append(ViewingBooking.scheduled_at >= date_from)
        if date_to:
            filters.append(ViewingBooking.scheduled_at <= date_to)
        q = select(ViewingBooking).join(Property, Property.id == ViewingBooking.property_id).where(and_(*filters))
        total = (await self.db.execute(select(func.count()).select_from(ViewingBooking).join(Property, Property.id == ViewingBooking.property_id).where(and_(*filters)))).scalar_one()
        order = ViewingBooking.scheduled_at.asc() if sort_order == "asc" else ViewingBooking.scheduled_at.desc()
        result = await self.db.execute(q.order_by(order).offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def create(self, **kwargs) -> ViewingBooking:
        booking = ViewingBooking(**kwargs)
        self.db.add(booking)
        await self.db.flush()
        return booking

    async def update(self, id: int, **kwargs) -> Optional[ViewingBooking]:
        await self.db.execute(update(ViewingBooking).where(ViewingBooking.id == id).values(**kwargs))
        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(update(ViewingBooking).where(ViewingBooking.id == id).values(status="cancelled"))
        return result.rowcount > 0
