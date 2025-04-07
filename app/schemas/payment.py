import uuid
from datetime import datetime

from pydantic import HttpUrl
from sqlmodel import SQLModel

from app.models.payment import PaymentBase, PaymentStatus


class PaymentCreate(PaymentBase):
    tier_id: uuid.UUID


class PaymentRead(PaymentBase):
    id: uuid.UUID
    user_id: uuid.UUID
    subscription_id: uuid.UUID | None
    tier_id: uuid.UUID
    stripe_checkout_session_id: str
    stripe_payment_intent_id: str | None
    amount: int
    currency: str
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime


class StripeCheckoutSession(SQLModel):
    session_id: str
    checkout_url: HttpUrl
