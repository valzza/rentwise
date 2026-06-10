from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Request

from app.repositories.user_repository import UserRepository
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
)
from app.core.config import settings
from app.schemas.auth_schemas import RegisterRequest, LoginRequest, TokenResponse
from app.models.user_models import User


class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, data: RegisterRequest, ip_address: str | None = None) -> TokenResponse:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        role = await self.repo.get_role_by_name(data.role)
        if not role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{data.role}' not found")

        user = await self.repo.create(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        # Self-registration: user is their own creator
        await self.repo.update_user(user.id, created_by=user.id, updated_by=user.id)
        await self.repo.assign_role(user.id, role.id)

        return await self._issue_tokens(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

        return await self._issue_tokens(user)

    async def refresh(self, token: str) -> TokenResponse:
        rt = await self.repo.get_refresh_token(token)

        if rt is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        if rt.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")
        if rt.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        # Rotate: revoke the old token and issue a fresh pair
        await self.repo.revoke_refresh_token(token)

        user = await self.repo.get_by_id(rt.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        return await self._issue_tokens(user)

    async def logout(self, token: str) -> None:
        await self.repo.revoke_refresh_token(token)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.repo.create_refresh_token(user.id, refresh_token, expires_at)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
