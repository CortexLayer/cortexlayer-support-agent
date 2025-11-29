"""SQLAlchemy model for agent handoff tickets when AI escalates to humans."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class HandoffStatus(str, enum.Enum):
    """Status values for escalation tickets."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class HandoffTicket(Base):
    """Represents a human support escalation triggered by the AI."""

    __tablename__ = "handoff_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    query_text = Column(Text, nullable=False)
    context = Column(Text, nullable=True)

    status = Column(Enum(HandoffStatus), default=HandoffStatus.OPEN)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationship
    client = relationship("Client", back_populates="handoff_tickets")
