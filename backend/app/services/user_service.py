from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user_models import User, Role, UserRole
from app.schemas.user_schemas import UserOut, UserUpdateRequest


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_me(self, current_user: User) -> UserOut:
        result = await self.db.execute(
            select(Role.name).join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == current_user.id)
        )
        roles = [r[0] for r in result.all()]
        data = UserOut.model_validate(current_user)
        data.roles = roles
        return data

    async def update_me(self, current_user: User, data: UserUpdateRequest) -> User:
        updates = data.model_dump(exclude_none=True)
        # Never allow self-service activation/deactivation
        updates.pop("is_active", None)
        for key, value in updates.items():
            setattr(current_user, key, value)
        await self.db.commit()
        await self.db.refresh(current_user)
        return current_user