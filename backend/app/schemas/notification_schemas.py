from datetime import datetime
from typing import List
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}
