from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user_models import User
from app.repositories.saved_property_repository import SavedPropertyRepository
from app.services.saved_property_service import SavedPropertyService
from app.schemas.property_schemas import PropertyOut

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> SavedPropertyService:
    return SavedPropertyService(SavedPropertyRepository(db))


@router.get("", response_model=List[PropertyOut])
async def list_saved(
    current_user: User = Depends(require_role("tenant")),
    svc: SavedPropertyService = Depends(_svc),
):
    return await svc.list(current_user.id)


@router.post("/{property_id}")
async def toggle_saved(
    property_id: int,
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
    svc: SavedPropertyService = Depends(_svc),
):
    saved = await svc.toggle(current_user.id, property_id)
    await db.commit()
    return {"property_id": property_id, "saved": saved}


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_saved(
    property_id: int,
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
    svc: SavedPropertyService = Depends(_svc),
):
    await svc.unsave(current_user.id, property_id)
    await db.commit()
