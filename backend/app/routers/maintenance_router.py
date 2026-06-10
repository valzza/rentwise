from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user_models import User
from app.repositories.maintenance_repository import MaintenanceRepository
from app.schemas.maintenance_schemas import MaintenanceCreateRequest, MaintenanceStatusUpdate, MaintenanceOut

router = APIRouter()


@router.post("", response_model=MaintenanceOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: MaintenanceCreateRequest,
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
):
    repo = MaintenanceRepository(db)
    req = await repo.create(
        property_id=data.property_id,
        tenant_id=current_user.id,
        title=data.title,
        description=data.description,
        priority=data.priority,
    )
    await db.commit()
    await db.refresh(req)
    return req


@router.get("", response_model=List[MaintenanceOut])
async def list_my_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = MaintenanceRepository(db)
    return await repo.get_for_tenant(current_user.id)


@router.put("/{request_id}", response_model=MaintenanceOut)
async def update_request_status(
    request_id: int,
    data: MaintenanceStatusUpdate,
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
):
    repo = MaintenanceRepository(db)
    updates = data.model_dump(exclude_none=True)
    req = await repo.update(request_id, **updates)
    await db.commit()
    return req
