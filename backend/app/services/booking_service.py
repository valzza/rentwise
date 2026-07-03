from fastapi import HTTPException, status

from app.repositories.booking_repository import BookingRepository
from app.services.notification_service import NotificationService
from app.models.user_models import User
from app.schemas.booking_schemas import BookingCreateRequest, BookingStatusUpdate


class BookingService:
    def __init__(self, repo: BookingRepository, notification_svc: NotificationService):
        self.repo = repo
        self.notification_svc = notification_svc

    async def create(self, data: BookingCreateRequest, current_user: User):
        return await self.repo.create(
            property_id=data.property_id,
            tenant_id=current_user.id,
            scheduled_at=data.scheduled_at,
            notes=data.notes,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

    async def get_my_bookings(self, user: User, role: str, status_filter, page, page_size,
                              date_from=None, date_to=None, sort_order="desc"):
        if role == "tenant":
            return await self.repo.get_for_tenant(user.id, status_filter, page, page_size,
                                                  date_from, date_to, sort_order)
        return await self.repo.get_for_landlord(user.id, status_filter, page, page_size,
                                                date_from, date_to, sort_order)

    async def update_status(self, booking_id: int, data: BookingStatusUpdate, current_user: User):
        booking = await self.repo.get_by_id(booking_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        valid_transitions = {
            "landlord": ["confirmed", "rejected"],
            "tenant": ["cancelled"],
        }

        updated = await self.repo.update(booking_id, status=data.status, updated_by=current_user.id)

        # Notify tenant when landlord changes status
        if data.status in ("confirmed", "rejected"):
            msg = f"Your viewing booking has been {data.status}."
            await self.notification_svc.notify(
                user_id=booking.tenant_id,
                type="booking_update",
                title=f"Booking {data.status.capitalize()}",
                message=msg,
            )

        return updated
