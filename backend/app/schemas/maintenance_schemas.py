from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MaintenanceCreateRequest(BaseModel):
    property_id: int
    title: str
    description: str
    priority: str = "medium"  # low | medium | high | urgent


class MaintenanceStatusUpdate(BaseModel):
    status: str   # pending | in_progress | resolved | closed
    priority: Optional[str] = None


class MaintenanceOut(BaseModel):
    id: int
    property_id: int
    tenant_id: int
    title: str
    description: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
