"""SQLAlchemy model for storing chat interactions between clients and the AI."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
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

    # Text
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)

    # RAG metadata
    retrieved_chunks = Column(JSONB, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Performance data
    latency_ms = Column(Integer, nullable=True)

    # Source channel
    channel = Column(String, default="api")  # api, whatsapp, widget

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    client = relationship("Client", back_populates="chat_logs")
