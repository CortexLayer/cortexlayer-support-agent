"""Application configuration."""

from __future__ import annotations

from typing import Literal

from dotenv import load_dotenv
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "CortexLayer Support Agent"
    DEBUG: bool = False
    ADMIN_API_KEY: str = ""
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://support-agent.dashboard.cortexlayertech.com",
    ]

    # Database / Cache
    DATABASE_URL: str
    REDIS_URL: str

    # Auth / JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI APIs
    OPENAI_API_KEY: str
    GROQ_API_KEY: str

    # Restrict to billable models only
    OPENAI_MODEL: Literal["gpt-4o-mini"] = "gpt-4o-mini"
    GROQ_MODEL: Literal["mixtral-8x7b"] = "mixtral-8x7b"

    # Embeddings
    OPENAI_EBD_MODEL: Literal["text-embedding-3-small"] = "text-embedding-3-small"

    # Storage
    DO_SPACES_KEY: str
    DO_SPACES_SECRET: str
    DO_SPACES_REGION: str = "blr1"
    DO_SPACES_BUCKET: str

    # Billing / Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # WhatsApp
    META_WHATSAPP_TOKEN: str
    META_WHATSAPP_APP_SECRET: str
    META_WHATSAPP_PHONE_ID: str

    # Observability
    SENTRY_DSN: str = ""

    # Validators

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        """Ensure JWT secret meets minimum security requirements."""
        if not value or len(value) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return value

    @field_validator(
        "OPENAI_MODEL",
        "GROQ_MODEL",
        "OPENAI_EBD_MODEL",
    )
    @classmethod
    def validate_model_names_are_billable(cls, value: str) -> str:
        """Ensure configured model names exist in billing PRICING."""
        from backend.app.services.billing import PRICING

        if value not in PRICING:
            raise ValueError(
                f"Model '{value}' has no pricing \
entry. Add it to billing.PRICING first."
            )
        return value

    @model_validator(mode="after")
    def validate_production_requirements(self) -> "Settings":
        """Ensure required settings are present in production."""
        if not self.DEBUG:
            missing = []

            if not self.JWT_SECRET:
                missing.append("JWT_SECRET")
            if not self.REDIS_URL:
                missing.append("REDIS_URL")
            if not self.STRIPE_SECRET_KEY:
                missing.append("STRIPE_SECRET_KEY")

            if missing:
                raise RuntimeError(
                    f"Missing required production settings: {missing}",
                )

        return self

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"


settings = Settings()


def validate_settings() -> None:
    """Force eager validation of settings at startup."""
    _ = settings
