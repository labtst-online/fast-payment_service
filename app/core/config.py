import os
from typing import Any

from pydantic import HttpUrl, PostgresDsn, field_validator
from pydantic_core import MultiHostUrl
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_path, extra='ignore')

    APP_ENV: str = "development"
    DOMAIN: str

    # Postgres Database Config
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Stripe Config
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # Kafka Config
    KAFKA_BOOTSTRAP_SERVERS="kafka:9092"
    KAFKA_PAYMENT_EVENTS_TOPIC="payment_events"
    KAFKA_CLIENT_ID: str = "payment_service_producer"

    # Service URLs
    AUTH_SERVICE_URL: HttpUrl = "http://auth_service:8000"
    SUBSCRIPTION_SERVICE_URL: HttpUrl = "http://subscription_service:8003"
    FRONTEND_URL: HttpUrl = "http://localhost:3000"

    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_async_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # If the URI is already provided as a string, use it directly
            return v
        # Otherwise, build it from components
        values = info.data
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )


settings = Settings()
