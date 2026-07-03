from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_audit_service
from app.schemas.auth_schemas import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
):
    service = AuthService(UserRepository(db), audit)
    tokens = await service.register(data, ip_address=_client_ip(request))
    await db.commit()
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
):
    service = AuthService(UserRepository(db), audit)
    tokens = await service.login(data, ip_address=_client_ip(request))
    await db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(UserRepository(db))
    tokens = await service.refresh(data.refresh_token)
    await db.commit()
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
):
    service = AuthService(UserRepository(db), audit)
    await service.logout(data.refresh_token, ip_address=_client_ip(request))
    await db.commit()