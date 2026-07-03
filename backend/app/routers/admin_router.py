from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role, require_permission, get_audit_service
from app.services.audit_service import AuditService
from app.services.admin_service import AdminService
from app.models.user_models import User
from app.schemas.user_schemas import UserUpdateRequest
from app.schemas.settings_schemas import SettingUpdateRequest

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(db)


@router.get("/users")
async def list_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_role("admin")),
    svc: AdminService = Depends(_svc),
):
    return await svc.list_users(search, role, is_active, page, page_size)


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Depends(require_permission("user:manage")),
    db: AsyncSession = Depends(get_db),
    svc: AdminService = Depends(_svc),
    audit: AuditService = Depends(get_audit_service),
):
    result = await svc.update_user(user_id, data.model_dump(exclude_none=True))
    await audit.log(action="update", entity="user", user_id=current_user.id,
                    entity_id=user_id, new_value=data.model_dump(exclude_none=True))
    await db.commit()
    return result


@router.get("/reports")
async def platform_reports(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    _: User = Depends(require_role("admin")),
    svc: AdminService = Depends(_svc),
):
    return await svc.reports(date_from, date_to)


@router.get("/properties")
async def all_properties(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_role("admin")),
    svc: AdminService = Depends(_svc),
):
    return await svc.all_properties(status, page, page_size)


@router.get("/audit-logs")
async def audit_logs(
    entity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_permission("audit:read")),
    svc: AdminService = Depends(_svc),
):
    return await svc.audit_logs(entity, page, page_size)


@router.get("/settings")
async def list_settings(
    _: User = Depends(require_role("admin")),
    svc: AdminService = Depends(_svc),
):
    return await svc.list_settings()


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    data: SettingUpdateRequest,
    current_user: User = Depends(require_permission("settings:manage")),
    db: AsyncSession = Depends(get_db),
    svc: AdminService = Depends(_svc),
    audit: AuditService = Depends(get_audit_service),
):
    result = await svc.update_setting(key, data.value)
    await audit.log(action="update", entity="setting", user_id=current_user.id,
                    new_value={"key": key, "value": data.value})
    await db.commit()
    return result