import logging

import httpx
import stripe
from auth_lib.auth import CurrentUserUUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, StripeCheckoutSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/checkout-session",
    response_model=StripeCheckoutSession,
    summary="Create Stripe Checkout Session",
    description="Initiates a payment process by creating a Stripe Checkout Session.",
    status_code=status.HTTP_200_OK,
)
async def create_checkout_session(
    payload: PaymentCreate,
    current_user: CurrentUserUUID,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Creates a Stripe Checkout Session for the given tier ID and authenticated user.
    """
    logger.info(f"User {current_user} requesting checkout session for tier {payload.tier_id}")
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.get(
                f"{settings.SUBSCRIPTION_SERVICE_URL}tier/tiers/{payload.tier_id}"
            )
            response.raise_for_status()
            tier_data = response.json()

            # Extract tier details from response
            tier_price = tier_data.get("price")
            tier_currency = tier_data.get("currency", "usd").lower()
            tier_name = tier_data.get("name")

            logger.info(f"Retrieved tier details: {tier_name} - {tier_price} {tier_currency}")

        except Exception as e:
            logger.exception(f"Failed to fetch tier price for {payload.tier_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not retrieve tier details for {payload.tier_id}.",
            )

    try:
        unit_amount_in_cents = int(round(tier_price * 100))
        logger.info(
            f"Converted price {tier_price} {tier_currency} to {unit_amount_in_cents} cents."
        )
    except Exception as e:
        logger.error(f"Failed to convert price {tier_price} to cents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process tier price.",
        )

    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=str(current_user),
            # Payment details
            line_items=[
                {
                    "price_data": {
                        "currency": tier_currency,
                        "product_data": {
                            "name": f"Subscription: {tier_name}",  # Display name on Stripe page
                        },
                        "unit_amount": unit_amount_in_cents,  # Price in cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=settings.DOMAIN + "?success=true",
            cancel_url=settings.DOMAIN + "?canceled=true",
            metadata={
                "tier_id": str(payload.tier_id),
                "user_id": str(current_user),
            },
        )
        logger.info(f"Stripe Checkout Session created successfully: {checkout_session.id}")

    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment session with Stripe: {e}",
        )
    except Exception as e:
        logger.error(f"Unexpected error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while initiating payment.",
        )

    db_payment = Payment(
        user_id=current_user,
        tier_id=payload.tier_id,
        stripe_checkout_session_id=checkout_session.id,
        amount=unit_amount_in_cents,
        currency=tier_currency,
        status=PaymentStatus.PENDING,
    )
    session.add(db_payment)

    try:
        await session.commit()
        await session.refresh(db_payment)
        logger.info(f"Pending payment record created in DB with ID: {db_payment.id}")
    except Exception as e:
        logger.critical(
            f"Failed to save pending payment record"
            f" for Stripe session {checkout_session.id} after creation. Error: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment session initiated but failed to save record. Please contact support.",
        )
    return StripeCheckoutSession(session_id=checkout_session.id, checkout_url=checkout_session.url)


# TODO: Add endpoint to check payment history
