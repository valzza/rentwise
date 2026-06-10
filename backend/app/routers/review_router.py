from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user_models import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.review_schemas import ReviewCreateRequest, ReviewOut

router = APIRouter()


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreateRequest,
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
):
    repo = ReviewRepository(db)

    if not await repo.has_completed_lease(current_user.id, data.property_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review properties where you have a completed lease",
        )
    if await repo.already_reviewed(current_user.id, data.property_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this property",
        )

    review = await repo.create(
        property_id=data.property_id,
        tenant_id=current_user.id,
        rating=data.rating,
        comment=data.comment,
    )
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/property/{property_id}", response_model=List[ReviewOut])
async def list_property_reviews(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    repo = ReviewRepository(db)
    return await repo.get_for_property(property_id)
