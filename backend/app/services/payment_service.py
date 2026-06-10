import stripe
from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.payment_repository import PaymentRepository
from app.repositories.lease_repository import LeaseRepository
from app.services.notification_service import NotificationService
from app.schemas.payment_schemas import PaymentIntentResponse

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        lease_repo: LeaseRepository,
        notification_svc: NotificationService,
    ):
        self.payment_repo = payment_repo
        self.lease_repo = lease_repo
        self.notification_svc = notification_svc

    async def create_payment_intent(self, lease_id: int, tenant_id: int) -> PaymentIntentResponse:
        lease = await self.lease_repo.get_by_id(lease_id)
        if not lease:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")
        if lease.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your lease")

        # Amount in cents — Stripe requires integer cents
        amount_cents = int(float(lease.deposit_amount) * 100)

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="eur",
            metadata={"lease_id": lease_id, "tenant_id": tenant_id},
        )

        payment = await self.payment_repo.create(
            lease_id=lease_id,
            tenant_id=tenant_id,
            amount=lease.deposit_amount,
            stripe_payment_id=intent["id"],
            type="deposit",
            status="pending",
        )

        return PaymentIntentResponse(
            client_secret=intent["client_secret"],
            payment_id=payment.id,
            amount=float(lease.deposit_amount),
        )

    async def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe signature")

        if event["type"] == "payment_intent.succeeded":
            pi = event["data"]["object"]
            await self._on_payment_succeeded(pi["id"], pi.get("metadata", {}))

        elif event["type"] == "payment_intent.payment_failed":
            pi = event["data"]["object"]
            await self._on_payment_failed(pi["id"], pi.get("metadata", {}))

    async def _on_payment_succeeded(self, stripe_payment_id: str, metadata: dict) -> None:
        payment = await self.payment_repo.get_by_stripe_id(stripe_payment_id)
        if not payment:
            return

        await self.payment_repo.update(payment.id, status="completed")

        # Mark lease as active once deposit is paid
        lease_id = int(metadata.get("lease_id", payment.lease_id))
        await self.lease_repo.update(lease_id, status="active")

        await self.notification_svc.notify(
            user_id=payment.tenant_id,
            type="payment_success",
            title="Payment Successful",
            message="Your deposit payment was received. Your lease is now active.",
        )

    async def _on_payment_failed(self, stripe_payment_id: str, metadata: dict) -> None:
        payment = await self.payment_repo.get_by_stripe_id(stripe_payment_id)
        if not payment:
            return

        await self.payment_repo.update(payment.id, status="failed")

        await self.notification_svc.notify(
            user_id=payment.tenant_id,
            type="payment_failed",
            title="Payment Failed",
            message="Your deposit payment failed. Please try again.",
        )
