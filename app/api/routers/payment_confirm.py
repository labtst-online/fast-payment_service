import logging

import stripe
from core.config import settings
from fastapi import APIRouter, HTTPException

from app.models.payment_confirm import ConfirmPaymentRequest

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/confirm-payment")
async def confirm_payment(confirm_payment_request: ConfirmPaymentRequest):
    try:
        intent = stripe.PaymentIntent.retrieve(confirm_payment_request.payment_intent_id)
        intent = stripe.PaymentIntent.confirm(confirm_payment_request.payment_intent_id)
        if intent.status == "succeeded":
            return {"message": "Payment successful"}
        else:
            return {"message": "Payment not successful", "status": intent.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
