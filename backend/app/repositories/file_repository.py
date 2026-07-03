from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit_models import File
from app.models.domain_models import PropertyImage


class FileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> File:
        f = File(**kwargs)
        self.db.add(f)
        await self.db.flush()
        return f

    async def get_by_id(self, file_id: int) -> Optional[File]:
        result = await self.db.execute(select(File).where(File.id == file_id))
        return result.scalar_one_or_none()

    async def link_property_image(self, property_id: int, file_id: int, is_primary: bool, created_by: int) -> PropertyImage:
        img = PropertyImage(
            property_id=property_id,
            file_id=file_id,
            is_primary=is_primary,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(img)
        await self.db.flush()
        return img

    async def property_has_images(self, property_id: int) -> bool:
        result = await self.db.execute(
            select(PropertyImage.id).where(PropertyImage.property_id == property_id).limit(1)
        )
        return result.scalar_one_or_none() is not None
