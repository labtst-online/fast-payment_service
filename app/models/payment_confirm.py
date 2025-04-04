from sqlmodel import SQLModel


class ConfirmPaymentRequest(SQLModel):
    payment_intent_id: str
