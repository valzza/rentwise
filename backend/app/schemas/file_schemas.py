from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FileOut(BaseModel):
    id: int
    entity: str
    entity_id: int
    filename: str
    file_path: str
    file_size: int
    created_at: datetime
    model_config = {"from_attributes": True}
