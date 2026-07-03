from typing import List
from fastapi import HTTPException, status

from app.repositories.lease_repository import LeaseRepository
from app.models.user_models import User
from app.schemas.lease_schemas import LeaseCreateRequest


class LeaseService:
    def __init__(self, repo: LeaseRepository):
        self.repo = repo

    async def create(self, data: LeaseCreateRequest, current_user: User):
        return await self.repo.create(
            property_id=data.property_id,
            tenant_id=data.tenant_id,
            landlord_id=current_user.id,
            start_date=data.start_date,
            end_date=data.end_date,
            monthly_rent=data.monthly_rent,
            deposit_amount=data.deposit_amount,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

    async def list_for_user(self, current_user: User, roles: List[str]) -> List:
        if "landlord" in roles or "admin" in roles:
            return await self.repo.get_for_landlord(current_user.id)
        return await self.repo.get_for_tenant(current_user.id)

    async def get(self, lease_id: int):
        lease = await self.repo.get_by_id(lease_id)
        if not lease:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")
        return lease