"""Usage tracking model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class UsageLog(Base):
    """Tracks billable operations per client."""

    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    # Operation details
    operation_type = Column(String, nullable=False, index=True)

    # Token tracking
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    embedding_tokens = Column(Integer, default=0)

    # Cost tracking
    cost_usd = Column(Float, default=0.0)

    # Metadata
    model_used = Column(String, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    client = relationship("Client", back_populates="usage_logs")
