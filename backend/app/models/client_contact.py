"""Client contact channels (WhatsApp, etc.)."""

import uuid

from sqlalchemy import Column, Enum, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class ContactChannel(str, Enum):
    """Supported external contact channels for clients."""

    WHATSAPP = "whatsapp"


class ClientContact(Base):
    """Maps external contact identifiers to a client."""

    __tablename__ = "client_contacts"
    __table_args__ = (
        UniqueConstraint("channel", "external_id", name="uq_contact_channel_external"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)

    channel = Column(String, nullable=False)  # "whatsapp"
    external_id = Column(String, nullable=False)  # phone number

    client = relationship("Client", backref="contacts")
