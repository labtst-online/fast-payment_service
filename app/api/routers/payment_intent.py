import logging

import stripe
from core.config import settings
from fastapi import APIRouter, HTTPException

from app.models.payment_intent_request import PaymentIntentRequest

logger = logging.getLogger(__name__)
router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-payment-intent")
async def create_payment_intent(payment_intent_request: PaymentIntentRequest):
    try:
        intent = stripe.PaymentIntent.create(
            amount=payment_intent_request.amount,
            currency=payment_intent_request.currency,
            description=payment_intent_request.description,
        )
        return {"client_secret": intent.client_secret}
    except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
