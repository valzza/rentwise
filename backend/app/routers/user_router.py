from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user_models import User
from app.services.user_service import UserService
from app.schemas.user_schemas import UserOut, UserUpdateRequest

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user),
    svc: UserService = Depends(_svc),
):
    return await svc.get_me(current_user)


@router.put("/me", response_model=UserOut)
async def update_me(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    svc: UserService = Depends(_svc),
):
    return await svc.update_me(current_user, data)