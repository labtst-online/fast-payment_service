import logging

import stripe
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        stripe_event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload data received from Stripe")
        raise HTTPException(status_code=400, detail="Invalid payload data")
    except stripe.error.SignatureVerificationError:
        logger.error("Stripe signature verification failed")
        raise HTTPException(status_code=400, detail="Signature verification failed")

    event_type = stripe_event.get("type")
    event_data = stripe_event.get("data", {}).get("object", {})

    if event_type == "payment_intent.succeeded":
        logger.info(f"Payment succeeded: {event_data}")
        # Implement business logic here
    else:
        logger.warning(f"Unhandled event type: {event_type}")

    return {"status": "success"}
