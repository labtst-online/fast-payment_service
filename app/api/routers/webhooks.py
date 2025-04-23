import datetime
import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.database import get_async_session
from app.core.kafka_client import kafka_client
from app.models.payment import Payment, PaymentStatus
from app.schemas.kafka_events import PaymentSucceededEvent

logger = logging.getLogger(__name__)
router = APIRouter()


async def verify_stripe_signature(request: Request) -> stripe.Event:
    """Verify Stripe webhook signature and return the event"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    logger.debug(f"Received Stripe webhook. Signature header present: {bool(sig_header)}")

    if not sig_header:
        logger.error("Stripe signature header missing.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature"
        )

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        logger.info(
            f"Stripe webhook signature verified successfully."
            f" Event ID: {event.id}, Type: {event.type}"
        )
        return event
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid Stripe webhook payload: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid Stripe webhook signature: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Unexpected error during webhook signature verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook signature verification error",
        )


async def process_successful_payment(
    session: AsyncSession, checkout_session_id: str, payment_intent_id: str
) -> Payment | None:
    """Update payment record for successful checkout"""
    logger.info(f"Processing successful payment for checkout session: {checkout_session_id}")
    statement = select(Payment).where(Payment.stripe_checkout_session_id == checkout_session_id)
    result = await session.execute(statement)
    db_payment = result.scalar_one_or_none()

    if not db_payment:
        logger.error(f"Payment record not found for session {checkout_session_id}")
        return None

    if db_payment.status == PaymentStatus.SUCCEEDED:
        logger.warning(
            f"Payment {checkout_session_id} already marked as SUCCEEDED. Skipping update."
        )
        return db_payment

    if db_payment.status != PaymentStatus.PENDING:
        logger.error(
            f"Payment {checkout_session_id} has unexpected status: {db_payment.status}."
            f" Expected PENDING."
        )
        return None

    try:
        db_payment.status = PaymentStatus.SUCCEEDED
        db_payment.stripe_payment_intent_id = payment_intent_id
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        logger.info(
            f"Payment record {db_payment.id} updated to SUCCEEDED for session {checkout_session_id}"
        )
        return db_payment
    except Exception as e:
        logger.exception(f"Database error updating payment {db_payment.id} to SUCCEEDED: {e}")
        await session.rollback()
        return None


async def publish_payment_event(payment: Payment) -> bool:
    """Publish payment success event to Kafka"""
    logger.info(f"Attempting to publish PaymentSucceededEvent for payment {payment.id}")
    try:
        event = PaymentSucceededEvent(
            payment_id=payment.id,
            user_id=payment.user_id,
            tier_id=payment.tier_id,
            amount=payment.amount,
            currency=payment.currency,
            paid_at=datetime.datetime.now(datetime.UTC),
            stripe_payment_intent_id=payment.stripe_payment_intent_id,
            stripe_checkout_session_id=payment.stripe_checkout_session_id,
        )
        logger.debug(f"Prepared event data for Kafka: {event.model_dump_json()}")

        success = kafka_client.produce_message(
            topic=settings.KAFKA_PAYMENT_EVENTS_TOPIC, event=event
        )

        if success:
            logger.info(
                f"Successfully published PaymentSucceededEvent to"
                f" Kafka topic '{settings.KAFKA_PAYMENT_EVENTS_TOPIC}' for payment {payment.id}."
            )
            return True
        else:
            logger.error(
                f"kafka_client.produce_message returned False for"
                f" payment {payment.id}. Check Kafka client logs."
            )
            return False

    except Exception as e:
        logger.exception(
            f"Error creating/publishing Kafka event for payment {payment.id}: {e}", exc_info=True
        )
        return False


@router.post(
    "/stripe",
    summary="Stripe Webhook Handler",
    description="Receives and processes webhook events from Stripe.",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,  # Hide this endpoint from OpenAPI docs
)
async def stripe_webhook(
    request: Request, session: AsyncSession = Depends(get_async_session)
) -> Response:
    """
    Handles incoming webhook events from Stripe.
    Verifies signature, processes relevant events (like checkout completion),
    updates local database, and publishes events to Kafka.
    """
    logger.info("Received Stripe webhook request.")

    # Verify Webhook Signature
    try:
        event = await verify_stripe_signature(request)
    except HTTPException as e:
        logger.error(f"Webhook signature verification failed: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error during signature verification step: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signature verification.",
        )

    event_type = event.get("type")
    logger.debug(f"Processing verified event type: {event_type}")

    if event_type != "checkout.session.completed":
        logger.info(f"Received unhandled event type: {event_type}. Acknowledging.")
        return Response(status_code=status.HTTP_200_OK)

    session_data = event["data"]["object"]
    checkout_session_id = session_data.get("id")
    payment_status = session_data.get("payment_status")
    payment_intent_id = session_data.get("payment_intent")

    logger.info(
        f"Handling checkout.session.completed for session {checkout_session_id}."
        f" Payment status: {payment_status}"
    )

    if payment_status != "paid":
        logger.warning(
            f"Checkout session {checkout_session_id} completed but payment"
            f" status is '{payment_status}'. No action taken."
        )
        return Response(status_code=status.HTTP_200_OK)

    if not payment_intent_id:
        logger.error(
            f"Checkout session {checkout_session_id} is paid but missing 'payment_intent'."
            " Cannot proceed."
        )
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Missing payment intent in webhook data.",
        )

    payment = None
    try:
        logger.debug(
            f"Attempting to process successful payment for"
            f" session {checkout_session_id} in database."
        )
        payment = await process_successful_payment(
            session=session,
            checkout_session_id=checkout_session_id,
            payment_intent_id=payment_intent_id,
        )

        if payment:
            logger.debug(
                f"Database update successful for payment {payment.id}."
                f" Attempting to publish Kafka event."
            )
            published = await publish_payment_event(payment)
            if not published:
                logger.error(
                    f"Failed to publish Kafka event for"
                    f" successfully processed payment {payment.id}."
                )
        else:
            logger.error(
                f"Failed to process payment in database for session {checkout_session_id}."
                f" No Kafka event published."
            )

    except Exception as e:
        logger.exception(
            f"Unhandled error processing payment for session {checkout_session_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing payment completion.",
        )

    logger.info(f"Successfully processed webhook for checkout session {checkout_session_id}.")
    return Response(status_code=status.HTTP_200_OK)
