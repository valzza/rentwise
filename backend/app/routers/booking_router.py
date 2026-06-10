from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user_models import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService
from app.schemas.booking_schemas import BookingCreateRequest, BookingStatusUpdate, BookingOut, PaginatedBookings

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> BookingService:
    return BookingService(BookingRepository(db), NotificationService(NotificationRepository(db)))


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreateRequest,
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
    svc: BookingService = Depends(_svc),
):
    booking = await svc.create(data, current_user)
    await db.commit()
    await db.refresh(booking)
    return booking


@router.get("", response_model=PaginatedBookings)
async def list_bookings(
    role: str = Query("tenant"),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    svc: BookingService = Depends(_svc),
):
    items, total = await svc.get_my_bookings(current_user, role, status_filter, page, page_size)
    return PaginatedBookings(items=items, total=total, page=page, page_size=page_size)


@router.put("/{booking_id}/status", response_model=BookingOut)
async def update_booking_status(
    booking_id: int,
    data: BookingStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: BookingService = Depends(_svc),
):
    booking = await svc.update_status(booking_id, data, current_user)
    await db.commit()
    return booking
