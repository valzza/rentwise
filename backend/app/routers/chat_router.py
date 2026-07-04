from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.dependencies import get_db, require_role, get_user_roles, get_current_user
from app.models.user_models import User
from app.repositories.mongo_repository import MongoRepository, chat_room_id
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

    tenants = []
    if tenant_ids:
        result = await db.execute(select(User).where(User.id.in_(tenant_ids)))
        users_by_id = {u.id: u for u in result.scalars().all()}
        for tid in tenant_ids:
            u = users_by_id.get(tid)
            tenants.append({
                "id": tid,
                "name": f"{u.first_name} {u.last_name}".strip() if u else f"User #{tid}",
            })

    return {"tenant_ids": tenant_ids, "tenants": tenants}


@router.get("/property/{property_id}/messages")
async def list_chat_messages(
    property_id: int,
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Load persisted chat history from MongoDB (used on page refresh)."""
    prop = await PropertyRepository(db).get_by_id(property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    uid = current_user.id
    roles = await get_user_roles(current_user, db)
    if "admin" not in roles and uid not in (prop.landlord_id, other_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed in this chat")

    room = chat_room_id(property_id, uid, other_user_id)
    messages = await MongoRepository().get_messages(room)
    return {"room_id": room, "messages": messages}