import math
from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select

from app.repositories.property_repository import PropertyRepository
from app.models.domain_models import Property
from app.models.user_models import User, Role, UserRole
from app.schemas.property_schemas import (
    PropertyCreateRequest, PropertyUpdateRequest,
    PropertySearchParams, PaginatedProperties, PropertyOut,
)


class PropertyService:
    def __init__(self, repo: PropertyRepository):
        self.repo = repo

    async def _role_names(self, user_id: int) -> List[str]:
        # Query roles explicitly — the User instance isn't loaded with its
        # relationships, and lazy-loading is unsafe under async SQLAlchemy.
        result = await self.repo.db.execute(
            select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
        )
        return [r[0] for r in result.all()]

    async def create_property(self, data: PropertyCreateRequest, current_user: User) -> Property:
        prop = await self.repo.create(
            landlord_id=current_user.id,
            created_by=current_user.id,
            title=data.title,
            description=data.description,
            price=data.price,
            city_id=data.city_id,
            neighborhood_id=data.neighborhood_id,
            size_m2=data.size_m2,
            num_rooms=data.num_rooms,
            num_bathrooms=data.num_bathrooms,
            is_furnished=data.is_furnished,
            is_pet_friendly=data.is_pet_friendly,
            amenity_ids=data.amenity_ids,
        )
        return prop

    async def get_property(self, property_id: int) -> PropertyOut:
        prop = await self.repo.get_by_id(property_id)
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        return PropertyOut.model_validate(prop)

    async def update_property(self, property_id: int, data: PropertyUpdateRequest, current_user: User) -> Property:
        prop = await self.repo.get_by_id(property_id)
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

        # Only owner or admin can update
        if prop.landlord_id != current_user.id:
            user_roles = await self._role_names(current_user.id)
            if "admin" not in user_roles:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this property")

        updates = data.model_dump(exclude_none=True)
        updates["updated_by"] = current_user.id
        return await self.repo.update(property_id, **updates)

    async def delete_property(self, property_id: int, current_user: User) -> None:
        prop = await self.repo.get_by_id(property_id)
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

        if prop.landlord_id != current_user.id:
            user_roles = await self._role_names(current_user.id)
            if "admin" not in user_roles:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        await self.repo.delete(property_id)

    async def search(self, params: PropertySearchParams, user_id: int | None = None) -> PaginatedProperties:
        items, total = await self.repo.search(params)

        # Log the search to MongoDB for analytics (degrades gracefully if Mongo is down)
        try:
            from app.repositories.mongo_repository import MongoRepository
            await MongoRepository().log_search(
                user_id=user_id,
                query_params=params.model_dump(exclude_none=True),
                results_count=total,
            )
        except Exception:
            pass

        pages = math.ceil(total / params.page_size) if params.page_size else 1
        return PaginatedProperties(
            items=[PropertyOut.model_validate(p) for p in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )

    async def get_featured(self) -> List[PropertyOut]:
        items = await self.repo.get_featured()
        return [PropertyOut.model_validate(p) for p in items]

    async def get_cities(self):
        return await self.repo.get_cities()

    async def get_neighborhoods(self, city_id=None):
        return await self.repo.get_neighborhoods(city_id)

    async def get_amenities(self):
        return await self.repo.get_amenities()