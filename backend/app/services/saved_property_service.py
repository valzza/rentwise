from typing import List

from app.repositories.saved_property_repository import SavedPropertyRepository
from app.schemas.property_schemas import PropertyOut


class SavedPropertyService:
    def __init__(self, repo: SavedPropertyRepository):
        self.repo = repo

    async def toggle(self, tenant_id: int, property_id: int) -> bool:
        """Save if not saved, unsave if already saved. Returns the new saved state."""
        existing = await self.repo.get(tenant_id, property_id)
        if existing:
            await self.repo.remove(tenant_id, property_id)
            return False
        await self.repo.add(tenant_id, property_id)
        return True

    async def unsave(self, tenant_id: int, property_id: int) -> None:
        await self.repo.remove(tenant_id, property_id)

    async def list(self, tenant_id: int) -> List[PropertyOut]:
        items = await self.repo.list_properties(tenant_id)
        return [PropertyOut.model_validate(p) for p in items]
