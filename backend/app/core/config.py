"""Pydantic Model for backend."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "CortexLayer Support Agent"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI APIs
    OPENAI_API_KEY: str
    GROQ_API_KEY: str

    # Storage
    DO_SPACES_KEY: str
    DO_SPACES_SECRET: str
    DO_SPACES_REGION: str = "blr1"
    DO_SPACES_BUCKET: str

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # WhatsApp
    META_WHATSAPP_TOKEN: str
    META_WHATSAPP_APP_SECRET: str
    META_WHATSAPP_PHONE_ID: str

    # Sentry
    SENTRY_DSN: str = ""

    class Config:
        """Pydantic Settings configuration."""

        env_file = ".env"


settings = Settings()
