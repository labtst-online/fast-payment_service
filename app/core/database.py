import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings

logger = logging.getLogger(__name__)


async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,
    echo=settings.APP_ENV == "development",
    future=True,
)


AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency for async session."""
    logger.debug("Creating payment async session")
    async with AsyncSessionFactory() as session:
        try:
            yield session
            logger.debug("Payment session yielded")
        except Exception:
            logger.exception("Payment session rollback because of exception")
            await session.rollback()
            raise
        finally:
            logger.debug("Payment session closed")
