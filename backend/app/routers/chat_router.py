from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role, get_user_roles
from app.models.user_models import User
from app.repositories.mongo_repository import MongoRepository
from app.repositories.property_repository import PropertyRepository

router = APIRouter()


@router.get("/property/{property_id}/partners")
async def list_chat_partners(
    property_id: int,
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """List tenant IDs who have chatted about this property (for landlord inbox)."""
    prop = await PropertyRepository(db).get_by_id(property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    roles = await get_user_roles(current_user, db)
    if "admin" not in roles and prop.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your property")

    landlord_id = prop.landlord_id
    tenant_ids = await MongoRepository().get_chat_partner_ids(property_id, landlord_id)
    return {"tenant_ids": tenant_ids}