from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class BookingCreateRequest(BaseModel):
    property_id: int
    scheduled_at: datetime
    notes: Optional[str] = None


class BookingStatusUpdate(BaseModel):
    status: str  # confirmed | rejected | cancelled | completed


class BookingOut(BaseModel):
    id: int
    property_id: int
    tenant_id: int
    scheduled_at: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PaginatedBookings(BaseModel):
    items: List[BookingOut]
    total: int
    page: int
    page_size: int
