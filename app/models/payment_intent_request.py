from sqlmodel import Field, SQLModel


class PaymentIntentRequest(SQLModel):
   amount: float = Field(ge=0.0)
   currency: str
   description: str = None
