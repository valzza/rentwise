from typing import Optional
from pydantic import BaseModel, field_validator


class PriceEstimateRequest(BaseModel):
    city_id: int
    neighborhood_id: Optional[int] = None
    size_m2: float
    num_rooms: int
    num_bathrooms: int
    is_furnished: bool = False
    is_pet_friendly: bool = False
    amenities_count: int = 0
    property_id: Optional[int] = None  # for logging purposes

    @field_validator("size_m2")
    @classmethod
    def positive_size(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("size_m2 must be positive")
        return v


class PriceEstimateResponse(BaseModel):
    suggested_price: float
    min_price: float
    max_price: float
    model_version: str
