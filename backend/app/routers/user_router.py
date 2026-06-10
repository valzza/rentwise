from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user_models import User, Role, UserRole
from app.schemas.user_schemas import UserOut, UserUpdateRequest

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    roles = [r[0] for r in result.all()]
    data = UserOut.model_validate(current_user)
    data.roles = roles
    return data


@router.put("/me", response_model=UserOut)
async def update_me(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updates = data.model_dump(exclude_none=True)
    # Never allow is_active to be self-set
    updates.pop("is_active", None)
    for key, value in updates.items():
        setattr(current_user, key, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user
