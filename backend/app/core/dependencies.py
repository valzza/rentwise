from typing import AsyncGenerator, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.models.user_models import User, UserRole, Role, RolePermission, Permission
from app.services.audit_service import AuditService
from app.repositories.audit_repository import AuditRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def get_user_roles(user: User, db: AsyncSession) -> List[str]:
    result = await db.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    return [row[0] for row in result.all()]


def require_role(*roles: str):
    """
    Dependency factory — raises 403 if the current user doesn't have at least one of the required roles.
    Usage: Depends(require_role("admin", "landlord"))
    """
    async def _check(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        user_roles = await get_user_roles(current_user, db)
        if not any(r in user_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {list(roles)}",
            )
        return current_user

    return _check


async def get_user_permissions(user: User, db: AsyncSession) -> List[str]:
    result = await db.execute(
        select(Permission.name)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user.id)
    )
    return [row[0] for row in result.all()]


def require_permission(*permissions: str):
    """
    Dependency factory — raises 403 unless the user's roles grant at least one
    of the named permissions. Usage: Depends(require_permission("property:create"))
    """
    async def _check(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        user_perms = await get_user_permissions(current_user, db)
        if not any(p in user_perms for p in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of permissions: {list(permissions)}",
            )
        return current_user

    return _check


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    """Shared dependency so any router/service can record audit-trail entries."""
    return AuditService(AuditRepository(db))