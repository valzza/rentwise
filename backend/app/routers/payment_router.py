from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user_models import User
from app.repositories.payment_repository import PaymentRepository
from app.repositories.lease_repository import LeaseRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.payment_service import PaymentService
from app.services.notification_service import NotificationService
from app.schemas.payment_schemas import PaymentIntentRequest, PaymentIntentResponse, PaymentOut, EarningsDashboard

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(
        PaymentRepository(db),
        LeaseRepository(db),
        NotificationService(NotificationRepository(db)),
    )


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    data: PaymentIntentRequest,
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
    svc: PaymentService = Depends(_svc),
):
    result = await svc.create_payment_intent(data.lease_id, current_user.id)
    await db.commit()
    return result


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
    svc: PaymentService = Depends(_svc),
):
    payload = await request.body()
    await svc.handle_webhook(payload, stripe_signature)
    await db.commit()
    return {"received": True}


@router.get("/my", response_model=list)
async def my_payments(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role("tenant")),
    db: AsyncSession = Depends(get_db),
):
    repo = PaymentRepository(db)
    items, total = await repo.get_for_tenant(current_user.id, status_filter, page, page_size)
    return items


@router.get("/earnings", response_model=EarningsDashboard)
async def landlord_earnings(
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
):
    repo = PaymentRepository(db)
    data = await repo.get_earnings_for_landlord(current_user.id)
    return data
