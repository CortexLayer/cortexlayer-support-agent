# Register all models when this package is imported.

from backend.app.models.chat_logs import ChatLog
from backend.app.models.client import Client
from backend.app.models.documents import Document
from backend.app.models.handoff import HandoffTicket
from backend.app.models.usage import UsageLog

__all__ = [
    "Client",
    "UsageLog",
    "Document",
    "ChatLog",
    "HandoffTicket",
]
