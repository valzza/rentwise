from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, extract

from app.models.domain_models import Payment, LeaseContract
from app.repositories.base_repository import AbstractRepository


class PaymentRepository(AbstractRepository[Payment]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> Optional[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[Payment]:
        result = await self.db.execute(select(Payment).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_by_stripe_id(self, stripe_id: str) -> Optional[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.stripe_payment_id == stripe_id))
        return result.scalar_one_or_none()

    async def get_for_tenant(self, tenant_id: int, status: Optional[str] = None, page: int = 1, page_size: int = 10) -> tuple:
        filters = [Payment.tenant_id == tenant_id]
        if status:
            filters.append(Payment.status == status)
        from sqlalchemy import and_
        total = (await self.db.execute(select(func.count()).select_from(Payment).where(and_(*filters)))).scalar_one()
        result = await self.db.execute(select(Payment).where(and_(*filters)).order_by(Payment.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    async def get_earnings_for_landlord(self, landlord_id: int) -> dict:
        """Aggregate completed payments for all leases owned by this landlord."""
        result = await self.db.execute(
            select(
                func.to_char(Payment.created_at, "YYYY-MM").label("month"),
                func.sum(Payment.amount).label("total"),
            )
            .join(LeaseContract, LeaseContract.id == Payment.lease_id)
            .where(LeaseContract.landlord_id == landlord_id, Payment.status == "completed")
            .group_by("month")
            .order_by("month")
        )
        rows = result.all()
        total = sum(r.total for r in rows)
        monthly = [{"month": r.month, "total": float(r.total)} for r in rows]
        return {"total_earned": float(total), "monthly": monthly}

    async def create(self, **kwargs) -> Payment:
        payment = Payment(**kwargs)
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def update(self, id: int, **kwargs) -> Optional[Payment]:
        await self.db.execute(update(Payment).where(Payment.id == id).values(**kwargs))
        return await self.get_by_id(id)

    async def delete(self, id: int) -> bool:
        return False  # Payments are immutable
