from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class RoleOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    roles: List[str] = []

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
