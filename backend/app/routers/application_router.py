from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_role, get_audit_service
from app.services.audit_service import AuditService
from app.models.user_models import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.application_service import ApplicationService
from app.services.notification_service import NotificationService
from app.schemas.application_schemas import ApplicationCreateRequest, ApplicationStatusUpdate, ApplicationOut, PaginatedApplications

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(ApplicationRepository(db), NotificationService(NotificationRepository(db)))


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreateRequest,
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
    svc: ApplicationService = Depends(_svc),
):
    app = await svc.create(data, current_user)
    await db.commit()
    await db.refresh(app)
    return app


@router.get("", response_model=PaginatedApplications)
async def list_my_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role("tenant")),
    svc: ApplicationService = Depends(_svc),
):
    items, total = await svc.get_for_tenant(current_user, status_filter, page, page_size)
    return PaginatedApplications(items=items, total=total, page=page, page_size=page_size)


@router.get("/landlord", response_model=PaginatedApplications)
async def list_landlord_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role("landlord", "admin")),
    svc: ApplicationService = Depends(_svc),
):
    items, total = await svc.get_for_landlord(
        current_user, status_filter, date_from, date_to, sort_order, page, page_size
    )
    return PaginatedApplications(items=items, total=total, page=page, page_size=page_size)


@router.get("/property/{property_id}", response_model=PaginatedApplications)
async def list_property_applications(
    property_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role("landlord", "admin")),
    svc: ApplicationService = Depends(_svc),
):
    items, total = await svc.get_for_property(property_id, status_filter, page, page_size)
    return PaginatedApplications(items=items, total=total, page=page, page_size=page_size)


@router.put("/{application_id}/status", response_model=ApplicationOut)
async def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
    svc: ApplicationService = Depends(_svc),
    audit: AuditService = Depends(get_audit_service),
):
    app = await svc.update_status(application_id, data, current_user)
    await audit.log(action="status_change", entity="application", user_id=current_user.id,
                    entity_id=application_id, new_value={"status": data.status})
    await db.commit()
    return app