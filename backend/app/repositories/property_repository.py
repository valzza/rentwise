from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.models.domain_models import (
    Property, PropertyAmenity, Amenity, City, Neighborhood,
    PropertyImage, Review
)
from app.repositories.base_repository import AbstractRepository
from app.schemas.property_schemas import PropertySearchParams


class PropertyRepository(AbstractRepository[Property]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> Optional[Property]:
        result = await self.db.execute(
            select(Property)
            .options(
                selectinload(Property.property_amenities).selectinload(PropertyAmenity.amenity),
                selectinload(Property.images).selectinload(PropertyImage.file),
                selectinload(Property.neighborhood),
            )
            .where(Property.id == id, Property.status != "deleted")
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[Property]:
        result = await self.db.execute(
            select(Property)
            .options(selectinload(Property.images))
            .where(Property.status == "active")
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Property:
        amenity_ids: List[int] = kwargs.pop("amenity_ids", [])
        prop = Property(**kwargs)
        self.db.add(prop)
        await self.db.flush()

        # Attach amenities
        for aid in amenity_ids:
            self.db.add(PropertyAmenity(property_id=prop.id, amenity_id=aid))

        # Set initial search vector
        await self._update_search_vector(prop.id, prop.title, prop.description or "")
        return prop

    async def update(self, id: int, **kwargs) -> Optional[Property]:
        amenity_ids: Optional[List[int]] = kwargs.pop("amenity_ids", None)
        if kwargs:
            await self.db.execute(update(Property).where(Property.id == id).values(**kwargs))

        if amenity_ids is not None:
            await self.db.execute(delete(PropertyAmenity).where(PropertyAmenity.property_id == id))
            for aid in amenity_ids:
                self.db.add(PropertyAmenity(property_id=id, amenity_id=aid))

        # Refresh search vector if title or description changed
        if "title" in kwargs or "description" in kwargs:
            prop = await self.get_by_id(id)
            if prop:
                await self._update_search_vector(id, prop.title, prop.description or "")

        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        """Soft delete — sets status to 'deleted'."""
        result = await self.db.execute(
            update(Property).where(Property.id == id).values(status="deleted")
        )
        return result.rowcount > 0

    async def search(self, params: PropertySearchParams) -> Tuple[List[Property], int]:
        filters = [Property.status == "active"]

        if params.city_id:
            filters.append(Property.city_id == params.city_id)
        if params.neighborhood_id:
            filters.append(Property.neighborhood_id == params.neighborhood_id)
        if params.min_price:
            filters.append(Property.price >= params.min_price)
        if params.max_price:
            filters.append(Property.price <= params.max_price)
        if params.num_rooms:
            filters.append(Property.num_rooms == params.num_rooms)
        if params.min_size:
            filters.append(Property.size_m2 >= params.min_size)
        if params.max_size:
            filters.append(Property.size_m2 <= params.max_size)
        if params.is_furnished is not None:
            filters.append(Property.is_furnished == params.is_furnished)
        if params.is_pet_friendly is not None:
            filters.append(Property.is_pet_friendly == params.is_pet_friendly)

        # Full-text search against the GIN-indexed tsvector column
        if params.q:
            filters.append(
                Property.search_vector.op("@@")(func.plainto_tsquery("english", params.q))
            )

        # Amenity filter — property must have ALL requested amenities
        if params.amenity_ids:
            for aid in params.amenity_ids:
                filters.append(
                    Property.id.in_(
                        select(PropertyAmenity.property_id).where(PropertyAmenity.amenity_id == aid)
                    )
                )

        # Count total matches
        count_result = await self.db.execute(
            select(func.count()).select_from(Property).where(and_(*filters))
        )
        total = count_result.scalar_one()

        # Determine sort column
        avg_rating_subq = (
            select(func.avg(Review.rating))
            .where(Review.property_id == Property.id)
            .correlate(Property)
            .scalar_subquery()
        )

        if params.sort_by == "price":
            order_col = Property.price
        elif params.sort_by == "rating":
            order_col = avg_rating_subq
        else:
            order_col = Property.created_at

        order_expr = order_col.desc() if params.sort_order == "desc" else order_col.asc()

        offset = (params.page - 1) * params.page_size
        result = await self.db.execute(
            select(Property)
            .options(
                selectinload(Property.property_amenities).selectinload(PropertyAmenity.amenity),
                selectinload(Property.images).selectinload(PropertyImage.file),
                selectinload(Property.neighborhood),
            )
            .where(and_(*filters))
            .order_by(order_expr)
            .offset(offset)
            .limit(params.page_size)
        )
        return list(result.scalars().all()), total

    async def get_featured(self, limit: int = 6) -> List[Property]:
        """Top N properties by average review rating."""
        avg_rating_subq = (
            select(func.avg(Review.rating))
            .where(Review.property_id == Property.id)
            .correlate(Property)
            .scalar_subquery()
        )
        result = await self.db.execute(
            select(Property)
            .options(
                selectinload(Property.images).selectinload(PropertyImage.file),
                selectinload(Property.neighborhood),
            )
            .where(Property.status == "active")
            .order_by(avg_rating_subq.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_cities(self) -> List[City]:
        result = await self.db.execute(select(City).order_by(City.name))
        return list(result.scalars().all())

    async def get_neighborhoods(self, city_id: Optional[int] = None) -> List[Neighborhood]:
        q = select(Neighborhood)
        if city_id:
            q = q.where(Neighborhood.city_id == city_id)
        result = await self.db.execute(q.order_by(Neighborhood.name))
        return list(result.scalars().all())

    async def get_amenities(self) -> List[Amenity]:
        result = await self.db.execute(select(Amenity).order_by(Amenity.name))
        return list(result.scalars().all())

    async def _update_search_vector(self, property_id: int, title: str, description: str) -> None:
        """Recompute the tsvector for full-text search after create/update.

        Includes the property's city name so searching by city (e.g. "Prishtina")
        matches. A DB trigger keeps this in sync too; this keeps the app correct
        even if the trigger is absent.
        """
        await self.db.execute(
            text(
                "UPDATE properties SET search_vector = to_tsvector('english', "
                ":title || ' ' || :description || ' ' || "
                "coalesce((SELECT name FROM cities WHERE id = properties.city_id), '')) "
                "WHERE id = :id"
            ),
            {"title": title, "description": description, "id": property_id},
        )
