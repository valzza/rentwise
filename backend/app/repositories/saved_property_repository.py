from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.domain_models import SavedProperty, Property, PropertyImage, PropertyAmenity
from sqlalchemy.orm import selectinload


class SavedPropertyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, tenant_id: int, property_id: int) -> Optional[SavedProperty]:
        result = await self.db.execute(
            select(SavedProperty).where(
                SavedProperty.tenant_id == tenant_id,
                SavedProperty.property_id == property_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, tenant_id: int, property_id: int) -> SavedProperty:
        sp = SavedProperty(
            tenant_id=tenant_id,
            property_id=property_id,
            created_by=tenant_id,
            updated_by=tenant_id,
        )
        self.db.add(sp)
        await self.db.flush()
        return sp

    async def remove(self, tenant_id: int, property_id: int) -> bool:
        result = await self.db.execute(
            delete(SavedProperty).where(
                SavedProperty.tenant_id == tenant_id,
                SavedProperty.property_id == property_id,
            )
        )
        return result.rowcount > 0

    async def list_properties(self, tenant_id: int) -> List[Property]:
        result = await self.db.execute(
            select(Property)
            .join(SavedProperty, SavedProperty.property_id == Property.id)
            .options(
                selectinload(Property.images).selectinload(PropertyImage.file),
                selectinload(Property.property_amenities).selectinload(PropertyAmenity.amenity),
                selectinload(Property.neighborhood),
            )
            .where(SavedProperty.tenant_id == tenant_id, Property.status != "deleted")
            .order_by(SavedProperty.saved_at.desc())
        )
        return list(result.scalars().all())
