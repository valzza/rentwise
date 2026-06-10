from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ApplicationCreateRequest(BaseModel):
    property_id: int
    message: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    status: str  # approved | rejected | withdrawn


class ApplicationOut(BaseModel):
    id: int
    property_id: int
    tenant_id: int
    message: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PaginatedApplications(BaseModel):
    items: List[ApplicationOut]
    total: int
    page: int
    page_size: int
