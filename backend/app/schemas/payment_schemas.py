from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class PaymentIntentRequest(BaseModel):
    lease_id: int


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_id: int
    amount: float


class PaymentOut(BaseModel):
    id: int
    lease_id: int
    tenant_id: int
    amount: float
    stripe_payment_id: Optional[str] = None
    type: str
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class EarningsMonthly(BaseModel):
    month: str
    total: float


class EarningsDashboard(BaseModel):
    total_earned: float
    monthly: List[EarningsMonthly]
