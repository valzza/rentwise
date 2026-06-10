from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class AmenityOut(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    model_config = {"from_attributes": True}


class CityOut(BaseModel):
    id: int
    name: str
    country: str
    model_config = {"from_attributes": True}


class NeighborhoodOut(BaseModel):
    id: int
    name: str
    city_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    model_config = {"from_attributes": True}


class PropertyImageOut(BaseModel):
    id: int
    file_id: int
    is_primary: bool
    file_path: Optional[str] = None
    model_config = {"from_attributes": True}


class PropertyCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    city_id: int
    neighborhood_id: Optional[int] = None
    size_m2: float
    num_rooms: int
    num_bathrooms: int
    is_furnished: bool = False
    is_pet_friendly: bool = False
    amenity_ids: List[int] = []

    @field_validator("price", "size_m2")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Must be positive")
        return v

    @field_validator("num_rooms", "num_bathrooms")
    @classmethod
    def at_least_one(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Must be at least 1")
        return v


class PropertyUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    neighborhood_id: Optional[int] = None
    size_m2: Optional[float] = None
    num_rooms: Optional[int] = None
    num_bathrooms: Optional[int] = None
    is_furnished: Optional[bool] = None
    is_pet_friendly: Optional[bool] = None
    status: Optional[str] = None
    amenity_ids: Optional[List[int]] = None


class PropertyOut(BaseModel):
    id: int
    landlord_id: int
    title: str
    description: Optional[str] = None
    price: float
    city_id: int
    neighborhood_id: Optional[int] = None
    size_m2: float
    num_rooms: int
    num_bathrooms: int
    is_furnished: bool
    is_pet_friendly: bool
    status: str
    amenities: List[AmenityOut] = []
    images: List[PropertyImageOut] = []
    neighborhood: Optional[NeighborhoodOut] = None
    avg_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "images") and obj.images:
            processed = []
            for img, schema_img in zip(obj.images, instance.images):
                if hasattr(img, "file") and img.file:
                    schema_img.file_path = img.file.file_path
                processed.append(schema_img)
            instance.images = processed
        if getattr(obj, "neighborhood", None):
            instance.neighborhood = NeighborhoodOut.model_validate(obj.neighborhood)
        return instance


class PropertySearchParams(BaseModel):
    q: Optional[str] = None
    city_id: Optional[int] = None
    neighborhood_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    num_rooms: Optional[int] = None
    min_size: Optional[float] = None
    max_size: Optional[float] = None
    is_furnished: Optional[bool] = None
    is_pet_friendly: Optional[bool] = None
    amenity_ids: Optional[List[int]] = None
    sort_by: str = "created_at"   # price | created_at | rating
    sort_order: str = "desc"      # asc | desc
    page: int = 1
    page_size: int = 12


class PaginatedProperties(BaseModel):
    items: List[PropertyOut]
    total: int
    page: int
    page_size: int
    pages: int
