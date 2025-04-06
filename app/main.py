import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.payment_confirm import router as confirm_router
from app.api.routers.payment_intent import router as intent_router
from app.api.routers.stripe_webhook import router as webhook_router
from app.models.payment_confirm import ConfirmPaymentRequest

from .core.config import settings
from .core.database import async_engine, get_async_session

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

    yield

    logger.info("Application shutdown...")
    # Close the engine connections pool
    await async_engine.dispose()
    logger.info("Database engine disposed.")


app = FastAPI(
    title="Payment Service",
    description="Handles user transactions.",
    version="0.1.0",
    lifespan=lifespan
)

@app.include_router(intent_router, prefix="/intent", tags=["IntentPayment"])

@app.include_router(confirm_router, prefix="/confirm", tags=["ConfirmPayment"])

@app.include_router(webhook_router, prefix="/webhook", tags=["WebhookPayment"])

@app.get("/test-db/", summary="Test Database Connection", tags=["Test"])
async def test_db_connection(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Attempts to retrieve the first tier from the database.
    """
    logger.info("Accessing /test-db/ endpoint")
    try:
        statement = select(ConfirmPaymentRequest).limit(1)
        result = await session.execute(statement)
        payment_ID = result.scalar_one_or_none()

        if payment_ID:
            logger.info(
                f"Successfully retrieved confirm_payment_ID: {payment_ID.payment_intent_id}"
            )
            return {"status": "success", "first_confirm_payment_ID": payment_ID.payment_intent_id}
        else:
            logger.info("No confirm_payment_ID found in the database.")
            return {"status": "success", "message": "No confirm_payment_ID found"}
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
