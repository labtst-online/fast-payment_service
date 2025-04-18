import uuid
from datetime import datetime
from typing import Literal

from sqlmodel import SQLModel


class PaymentSucceededEvent(SQLModel):
    event_type: Literal["payment.succeeded"] = "payment.succeeded"
    payment_id: uuid.UUID
    user_id: uuid.UUID
    tier_id: uuid.UUID
    amount: int
    currency: str
    paid_at: datetime
    stripe_payment_intent_id: str | None = None
    stripe_checkout_session_id: str


class PaymentFailedEvent(SQLModel):
    event_type: Literal["payment.failed"] = "payment.failed"
    payment_id: uuid.UUID
    user_id: uuid.UUID
    tier_id: uuid.UUID
    failed_at: datetime
    reason: str | None = None
    stripe_checkout_session_id: str
