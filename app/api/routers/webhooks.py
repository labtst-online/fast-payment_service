import logging
from datetime import datetime

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
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        logger.debug(f"Stripe webhook signature verified successfully."
                     f" Event ID: {event.id}, Type: {event.type}")
        return event
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid Stripe webhook payload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid Stripe webhook signature: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    except Exception as e:
        logger.error(f"Unexpected error during webhook signature verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook signature verification error"
        )


async def process_successful_payment(
    session: AsyncSession,
    checkout_session_id: str,
    payment_intent_id: str
) -> Payment:
    """Update payment record for successful checkout"""
    statement = select(Payment).where(Payment.stripe_checkout_session_id == checkout_session_id)
    result = await session.execute(statement)
    db_payment = result.scalar_one_or_none()

    if not db_payment:
        logger.error(f"Payment record not found for session {checkout_session_id}")
        return None

    if db_payment.status == PaymentStatus.SUCCEEDED:
        logger.warning(f"Payment {checkout_session_id} already marked as SUCCEEDED")
        return db_payment

    if db_payment.status != PaymentStatus.PENDING:
        logger.error(f"Payment {checkout_session_id} has invalid status: {db_payment.status}")
        return None

    db_payment.status = PaymentStatus.SUCCEEDED
    db_payment.stripe_payment_intent_id = payment_intent_id
    session.add(db_payment)
    await session.commit()
    await session.refresh(db_payment)

    return db_payment


async def publish_payment_event(payment: Payment) -> bool:
    """Publish payment success event to Kafka"""
    try:
        event = PaymentSucceededEvent(
            payment_id=payment.id,
            user_id=payment.user_id,
            tier_id=payment.tier_id,
            amount=payment.amount,
            currency=payment.currency,
            paid_at=datetime.now(datetime.UTC),
            stripe_payment_intent_id=payment.stripe_payment_intent_id,
            stripe_checkout_session_id=payment.stripe_checkout_session_id
        )

        success = kafka_client.produce_message(
            topic=settings.KAFKA_PAYMENT_EVENTS_TOPIC,
            event=event
        )

        if success:
            logger.info(f"Published PaymentSucceededEvent to Kafka for payment {payment.id}.")
            return True

        logger.error(f"Failed to publish event for payment {payment.id}")
        return False

    except Exception as e:
        logger.exception(
            f"Error creating/publishing Kafka event for payment {payment.id}: {e}",
            exc_info=True
        )
        return False


@router.post(
    "/stripe",
    summary="Stripe Webhook Handler",
    description="Receives and processes webhook events from Stripe.",
    status_code=status.HTTP_200_OK,
    include_in_schema=False # Hide this endpoint from OpenAPI docs
)
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
) -> Response:
    """
    Handles incoming webhook events from Stripe.
    Verifies signature, processes relevant events (like checkout completion),
    updates local database, and publishes events to Kafka.
    """
    logger.info("Received Stripe webhook request.")

    # Verify Webhook Signature
    event = await verify_stripe_signature(request)

    if event['type'] != 'checkout.session.completed':
        logger.info(f"Received unhandled event type: {event['type']}")
        return Response(status_code=status.HTTP_200_OK)

    # Handle the 'checkout.session.completed' event
    session_data = event['data']['object']
    if session_data.get('payment_status') != 'paid':
        logger.warning(f"Checkout {session_data['id']} not paid")
        return Response(status_code=status.HTTP_200_OK)


    # Update Database
    try:
        payment = await process_successful_payment(
            session=session,
            checkout_session_id=session_data['id'],
            payment_intent_id=session_data.get('payment_intent')
        )
        # Publish to Kafka
        if payment:
            await publish_payment_event(payment)

    except Exception as e:
        logger.exception(f"Error processing payment: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment"
        )

    return Response(status_code=status.HTTP_200_OK)
