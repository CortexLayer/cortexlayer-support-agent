"""SQLAlchemy model for uploaded documents."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class Document(Base):
    """Represents a document uploaded by a client into CortexLayer."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    filename = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # pdf, txt, url
    source_url = Column(String, nullable=True)

    file_size_bytes = Column(Integer, nullable=False)
    chunk_count = Column(Integer, default=0)

    s3_key = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # relationships
    client = relationship("Client", back_populates="documents")
