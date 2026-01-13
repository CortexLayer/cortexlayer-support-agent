"""Schemas for WhatsApp webhook payloads."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class WhatsAppMessage(BaseModel):
    """Normalized representation of a WhatsApp message."""

    from_number: str
    message_id: str
    timestamp: str
    text: Optional[str] = None
    type: str


class WhatsAppWebhookEntry(BaseModel):
    """Single webhook entry sent by Meta."""

    id: str
    changes: List[Dict[str, Any]]


class WhatsAppWebhook(BaseModel):
    """Top-level WhatsApp webhook payload."""

    object: str
    entry: List[WhatsAppWebhookEntry]
