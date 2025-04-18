import logging
from contextlib import asynccontextmanager

import stripe
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.payment import router as payment_router
from app.api.routers.webhooks import router as webhooks_router
from app.models.payment import Payment

from .core.config import settings
from .core.database import async_engine, get_async_session
from .core.kafka_client import kafka_client

# Configure logging
# Basic config, customize as needed (e.g., structured logging)
logging.basicConfig(level=logging.INFO if settings.APP_ENV == "production" else logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    # You can add startup logic here, like checking DB connection
    try:
        async with async_engine.connect():
            logger.info("Database connection successful during startup.")
    except Exception as e:
        logger.error(f"Database connection failed during startup: {e}")

    # Initialize Stripe API Key
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        logger.info("Stripe API key configured successfully during startup.")
    except Exception:
        logger.exception("CRITICAL: Failed to configure Stripe API key on startup.", exc_info=True)

    # Inittialize Kafka Producer
    logger.info("Initializing Kafka producer...")
    try:
        kafka_client.init_producer()
        logger.info("Kafka Producer initialized successfully during startup.")
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred "
            f"during Kafka producer initialization: {e}", exc_info=True
        )
        raise RuntimeError("Kafka producer initialization failed") from e

    yield
    logger.info("Application shutdown...")
    # Close the engine connections pool
    await async_engine.dispose()
    logger.info("Database engine disposed.")

    logger.info("Close Kafka Producer")
    kafka_client.close_producer()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Payment Service",
    description="Handles user transactions.",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(webhooks_router, prefix="/webhooks", tags=["WebhookPayment"])

app.include_router(payment_router, prefix="/payment", tags=["Payment"])

@app.get("/test-db/", summary="Test Database Connection", tags=["Test"])
async def test_db_connection(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Attempts to retrieve the first payment_ID from the database.
    """
    logger.info("Accessing /test-db/ endpoint")
    try:
        statement = select(Payment).limit(1)
        result = await session.execute(statement)
        payment = result.scalar_one_or_none()

        if payment:
            logger.info(
                f"Successfully retrieved payment_ID: {payment.id}"
            )
            return {"status": "success", "first_payment_ID": payment.id}
        else:
            logger.info("No payment_ID found in the database.")
            return {"status": "success", "message": "No payment_ID found"}
    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/", summary="Health Check", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "Payment Service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
       "app.main:app",
       host="0.0.0.0",
       port=8004, # Or load from config
       reload=(settings.APP_ENV == "development"),
       log_level="info"
   )
