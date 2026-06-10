from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import anthropic

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user_models import User
from app.repositories.property_repository import PropertyRepository
from app.services.property_service import PropertyService
from app.schemas.property_schemas import (
    PropertyCreateRequest, PropertyUpdateRequest, PropertyOut,
    PaginatedProperties, PropertySearchParams,
    CityOut, NeighborhoodOut, AmenityOut,
)


class GenerateDescriptionRequest(BaseModel):
    bullet_points: str


class GenerateDescriptionResponse(BaseModel):
    description: str

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> PropertyService:
    return PropertyService(PropertyRepository(db))


@router.get("/search", response_model=PaginatedProperties)
async def search_properties(
    q: Optional[str] = Query(None),
    city_id: Optional[int] = Query(None),
    neighborhood_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    num_rooms: Optional[int] = Query(None),
    min_size: Optional[float] = Query(None),
    max_size: Optional[float] = Query(None),
    is_furnished: Optional[bool] = Query(None),
    is_pet_friendly: Optional[bool] = Query(None),
    amenity_ids: Optional[List[int]] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    svc: PropertyService = Depends(_svc),
):
    params = PropertySearchParams(
        q=q, city_id=city_id, neighborhood_id=neighborhood_id,
        min_price=min_price, max_price=max_price, num_rooms=num_rooms,
        min_size=min_size, max_size=max_size, is_furnished=is_furnished,
        is_pet_friendly=is_pet_friendly, amenity_ids=amenity_ids,
        sort_by=sort_by, sort_order=sort_order, page=page, page_size=page_size,
    )
    return await svc.search(params)


@router.get("/featured", response_model=List[PropertyOut])
async def get_featured(svc: PropertyService = Depends(_svc)):
    return await svc.get_featured()


@router.get("/cities", response_model=List[CityOut])
async def list_cities(svc: PropertyService = Depends(_svc)):
    return await svc.get_cities()


@router.get("/neighborhoods", response_model=List[NeighborhoodOut])
async def list_neighborhoods(
    city_id: Optional[int] = Query(None),
    svc: PropertyService = Depends(_svc),
):
    return await svc.get_neighborhoods(city_id)


@router.get("/amenities", response_model=List[AmenityOut])
async def list_amenities(svc: PropertyService = Depends(_svc)):
    return await svc.get_amenities()


@router.get("", response_model=PaginatedProperties)
async def list_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    svc: PropertyService = Depends(_svc),
):
    params = PropertySearchParams(page=page, page_size=page_size)
    return await svc.search(params)


@router.post("", response_model=PropertyOut, status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreateRequest,
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
    svc: PropertyService = Depends(_svc),
):
    prop = await svc.create_property(data, current_user)
    await db.commit()
    await db.refresh(prop)
    return prop


@router.post("/generate-description", response_model=GenerateDescriptionResponse)
async def generate_description(
    data: GenerateDescriptionRequest,
    current_user: User = Depends(require_role("landlord", "admin")),
):
    if settings.ANTHROPIC_API_KEY == "sk-ant-placeholder":
        raise HTTPException(status_code=503, detail="Anthropic API key not configured.")
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                "Write a professional, engaging rental property description in 2-3 sentences "
                "based on these features. Be concise and highlight the most appealing aspects. "
                "Do not use bullet points in the output — write flowing prose only.\n\n"
                f"Features:\n{data.bullet_points}"
            ),
        }],
    )
    return {"description": message.content[0].text.strip()}


@router.get("/{property_id}", response_model=PropertyOut)
async def get_property(
    property_id: int,
    svc: PropertyService = Depends(_svc),
):
    return await svc.get_property(property_id)


@router.put("/{property_id}", response_model=PropertyOut)
async def update_property(
    property_id: int,
    data: PropertyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: PropertyService = Depends(_svc),
):
    prop = await svc.update_property(property_id, data, current_user)
    await db.commit()
    return prop


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: PropertyService = Depends(_svc),
):
    await svc.delete_property(property_id, current_user)
    await db.commit()
