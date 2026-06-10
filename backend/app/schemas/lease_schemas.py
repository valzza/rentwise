from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


class LeaseCreateRequest(BaseModel):
    property_id: int
    tenant_id: int
    start_date: date
    end_date: date
    monthly_rent: float
    deposit_amount: float


class LeaseOut(BaseModel):
    id: int
    property_id: int
    tenant_id: int
    landlord_id: int
    start_date: date
    end_date: date
    monthly_rent: float
    deposit_amount: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
