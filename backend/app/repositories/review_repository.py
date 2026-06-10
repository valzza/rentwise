from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.domain_models import Review, LeaseContract
from app.repositories.base_repository import AbstractRepository


class ReviewRepository(AbstractRepository[Review]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> Optional[Review]:
        result = await self.db.execute(select(Review).where(Review.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[Review]:
        result = await self.db.execute(select(Review).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_for_property(self, property_id: int) -> List[Review]:
        result = await self.db.execute(select(Review).where(Review.property_id == property_id).order_by(Review.created_at.desc()))
        return list(result.scalars().all())

    async def has_completed_lease(self, tenant_id: int, property_id: int) -> bool:
        """Only tenants with a completed lease on the property may leave a review."""
        result = await self.db.execute(
            select(LeaseContract).where(
                LeaseContract.tenant_id == tenant_id,
                LeaseContract.property_id == property_id,
                LeaseContract.status == "completed",
            )
        )
        return result.scalar_one_or_none() is not None

    async def already_reviewed(self, tenant_id: int, property_id: int) -> bool:
        result = await self.db.execute(
            select(Review).where(Review.tenant_id == tenant_id, Review.property_id == property_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, **kwargs) -> Review:
        review = Review(**kwargs)
        self.db.add(review)
        await self.db.flush()
        return review

    async def update(self, id: int, **kwargs) -> Optional[Review]:
        await self.db.execute(update(Review).where(Review.id == id).values(**kwargs))
        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(select(Review).where(Review.id == id))
        review = result.scalar_one_or_none()
        if review:
            await self.db.delete(review)
            return True
        return False
