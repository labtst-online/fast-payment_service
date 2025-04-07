import datetime
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, func
from sqlmodel import Field, SQLModel


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentBase(SQLModel):
    pass


class Payment(PaymentBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    user_id: uuid.UUID = Field(index=True, nullable=False)
    subscription_id: uuid.UUID | None = Field(index=True, default=None, nullable=True)
    tier_id: uuid.UUID = Field(index=True, nullable=False)
    stripe_checkout_session_id: str = Field(index=True, unique=True, nullable=False)
    stripe_payment_intent_id: str | None = Field(index=True, default=None, nullable=True)
    amount: int = Field(ge=0, nullable=False)  # Store cents
    currency: str = Field(default="usd", nullable=False, max_length=3)
    status: PaymentStatus = Field(
        sa_column=Column(
            Enum(PaymentStatus), nullable=False, index=True,
        )
    )
    created_at: datetime.datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
    updated_at: datetime.datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )
