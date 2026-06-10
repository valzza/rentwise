from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class ReviewCreateRequest(BaseModel):
    property_id: int
    rating: int
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewOut(BaseModel):
    id: int
    property_id: int
    tenant_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}
