"""Send WhatsApp messages via Meta Graph API (async)."""

import httpx

from backend.app.core.config import settings
from backend.app.utils.logger import logger

META_API_BASE = "https://graph.facebook.com/v15.0"


async def send_whatsapp_message(to_number: str, message: str) -> bool:
    """Send a text message using Meta WhatsApp Cloud API.

    Returns True on success, False on failure.
    """
    if not settings.META_WHATSAPP_TOKEN or not settings.META_WHATSAPP_PHONE_ID:
        logger.error("WhatsApp settings missing: cannot send message")
        return False

    url = f"{META_API_BASE}/{settings.META_WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message},
    }
    headers = {"Authorization": f"Bearer {settings.META_WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            logger.info("WhatsApp message sent to %s", to_number)
            return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "WhatsApp send failed (status %s): %s",
                exc.response.status_code,
                exc.response.text,
            )
        except Exception as exc:
            logger.error("WhatsApp send error: %s", exc)
    return False
