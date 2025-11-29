"""Client model for authentication, billing and plan management."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID

from backend.app.core.database import Base


class PlanType(str, enum.Enum):
    """Subscription plan types."""

    STARTER = "starter"
    GROWTH = "growth"
    SCALE = "scale"


class BillingStatus(str, enum.Enum):
    """Billing lifecycle states for a client."""

    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    DISABLED = "disabled"


class Client(Base):
    """Client account, subscription plan, and billing information."""

    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    company_name = Column(String, nullable=False)

    # Plan & Billing
    plan_type = Column(Enum(PlanType), default=PlanType.STARTER)
    billing_status = Column(Enum(BillingStatus), default=BillingStatus.ACTIVE)

    # Stripe
    stripe_customer_id = Column(String, unique=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)

    # Flags
    is_active = Column(Boolean, default=True)
    is_disabled = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
