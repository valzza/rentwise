from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user_models import User
from app.repositories.lease_repository import LeaseRepository
from app.schemas.lease_schemas import LeaseCreateRequest, LeaseOut

router = APIRouter()


@router.post("", response_model=LeaseOut, status_code=status.HTTP_201_CREATED)
async def create_lease(
    data: LeaseCreateRequest,
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
):
    repo = LeaseRepository(db)
    lease = await repo.create(
        property_id=data.property_id,
        tenant_id=data.tenant_id,
        landlord_id=current_user.id,
        start_date=data.start_date,
        end_date=data.end_date,
        monthly_rent=data.monthly_rent,
        deposit_amount=data.deposit_amount,
    )
    await db.commit()
    await db.refresh(lease)
    return lease


@router.get("", response_model=List[LeaseOut])
async def list_my_leases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = LeaseRepository(db)
    user_roles = [ur.role.name for ur in current_user.user_roles] if current_user.user_roles else []
    if "landlord" in user_roles or "admin" in user_roles:
        return await repo.get_for_landlord(current_user.id)
    return await repo.get_for_tenant(current_user.id)


@router.get("/{lease_id}", response_model=LeaseOut)
async def get_lease(
    lease_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = LeaseRepository(db)
    lease = await repo.get_by_id(lease_id)
    if not lease:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lease not found")
    return lease
