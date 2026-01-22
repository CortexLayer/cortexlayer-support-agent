"""SQLAlchemy model for storing chat interactions between clients and the AI."""

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
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class ChatLog(Base):
    """Represents a single chat exchange including query/response & metadata."""

    __tablename__ = "chat_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)

    retrieved_chunks = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)

    latency_ms = Column(Integer, nullable=True)

    channel = Column(String, default="api")

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    client = relationship("Client", back_populates="chat_logs")
