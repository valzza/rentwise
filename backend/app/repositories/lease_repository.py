from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.domain_models import LeaseContract
from app.repositories.base_repository import AbstractRepository


class LeaseRepository(AbstractRepository[LeaseContract]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> Optional[LeaseContract]:
        result = await self.db.execute(select(LeaseContract).where(LeaseContract.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[LeaseContract]:
        result = await self.db.execute(select(LeaseContract).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_for_tenant(self, tenant_id: int) -> List[LeaseContract]:
        result = await self.db.execute(select(LeaseContract).where(LeaseContract.tenant_id == tenant_id).order_by(LeaseContract.created_at.desc()))
        return list(result.scalars().all())

    async def get_for_landlord(self, landlord_id: int) -> List[LeaseContract]:
        result = await self.db.execute(select(LeaseContract).where(LeaseContract.landlord_id == landlord_id).order_by(LeaseContract.created_at.desc()))
        return list(result.scalars().all())

    async def create(self, **kwargs) -> LeaseContract:
        lease = LeaseContract(**kwargs)
        self.db.add(lease)
        await self.db.flush()
        return lease

    async def update(self, id: int, **kwargs) -> Optional[LeaseContract]:
        await self.db.execute(update(LeaseContract).where(LeaseContract.id == id).values(**kwargs))
        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(update(LeaseContract).where(LeaseContract.id == id).values(status="terminated"))
        return result.rowcount > 0
