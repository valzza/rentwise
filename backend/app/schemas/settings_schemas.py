from typing import Optional
from pydantic import BaseModel


class SettingOut(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str] = None
    model_config = {"from_attributes": True}


class SettingUpdateRequest(BaseModel):
    value: str
