"""WhatsApp outbound message sender."""

import httpx

from backend.app.core.config import settings
from backend.app.utils.logger import logger


async def send_whatsapp_message(
    to_number: str,
    message: str,
) -> None:
    """Send a WhatsApp text message via Meta API."""
    url = f"https://graph.facebook.com/v18.0/{settings.META_WHATSAPP_PHONE_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message},
    }

    headers = {
        "Authorization": f"Bearer {settings.META_WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code >= 400:
        logger.error(
            "WhatsApp send failed",
            extra={"status": response.status_code, "body": response.text},
        )
        raise RuntimeError("Failed to send WhatsApp message")
