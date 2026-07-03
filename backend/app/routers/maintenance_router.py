from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user_models import User
from app.repositories.maintenance_repository import MaintenanceRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.maintenance_service import MaintenanceService
from app.services.notification_service import NotificationService
from app.schemas.maintenance_schemas import MaintenanceCreateRequest, MaintenanceStatusUpdate, MaintenanceOut

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> MaintenanceService:
    return MaintenanceService(MaintenanceRepository(db), NotificationService(NotificationRepository(db)))


@router.post("", response_model=MaintenanceOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: MaintenanceCreateRequest,
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
    svc: MaintenanceService = Depends(_svc),
):
    req = await svc.create(data, current_user)
    await db.commit()
    await db.refresh(req)
    return req


@router.get("", response_model=List[MaintenanceOut])
async def list_my_requests(
    current_user: User = Depends(require_role("tenant")),
    svc: MaintenanceService = Depends(_svc),
):
    return await svc.list_for_tenant(current_user)


@router.get("/landlord", response_model=List[MaintenanceOut])
async def list_landlord_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    property_id: Optional[int] = Query(None),
    current_user: User = Depends(require_role("landlord", "admin")),
    svc: MaintenanceService = Depends(_svc),
):
    return await svc.search_for_landlord(current_user, status_filter, priority, property_id)


@router.put("/{request_id}", response_model=MaintenanceOut)
async def update_request_status(
    request_id: int,
    data: MaintenanceStatusUpdate,
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
    svc: MaintenanceService = Depends(_svc),
):
    req = await svc.update_status(request_id, data, current_user)
    await db.commit()
    return req