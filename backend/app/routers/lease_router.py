from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_role, get_audit_service, get_user_roles
from app.services.audit_service import AuditService
from app.models.user_models import User
from app.repositories.lease_repository import LeaseRepository
from app.services.lease_service import LeaseService
from app.schemas.lease_schemas import LeaseCreateRequest, LeaseOut

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> LeaseService:
    return LeaseService(LeaseRepository(db))


@router.post("", response_model=LeaseOut, status_code=status.HTTP_201_CREATED)
async def create_lease(
    data: LeaseCreateRequest,
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
    svc: LeaseService = Depends(_svc),
    audit: AuditService = Depends(get_audit_service),
):
    lease = await svc.create(data, current_user)
    await audit.log(action="create", entity="lease", user_id=current_user.id,
                    entity_id=lease.id, new_value={"property_id": data.property_id, "tenant_id": data.tenant_id})
    await db.commit()
    await db.refresh(lease)
    return lease


@router.get("", response_model=List[LeaseOut])
async def list_my_leases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: LeaseService = Depends(_svc),
):
    roles = await get_user_roles(current_user, db)
    return await svc.list_for_user(current_user, roles)


@router.get("/{lease_id}", response_model=LeaseOut)
async def get_lease(
    lease_id: int,
    current_user: User = Depends(get_current_user),
    svc: LeaseService = Depends(_svc),
):
    return await svc.get(lease_id)
lease_router.py