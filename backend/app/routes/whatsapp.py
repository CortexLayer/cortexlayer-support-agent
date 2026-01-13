"""WhatsApp webhook endpoints."""

import hashlib
import hmac

from fastapi import APIRouter, HTTPException, Query, Request

from backend.app.core.config import settings
from backend.app.schemas.whatsapp import WhatsAppWebhook
from backend.app.utils.logger import logger

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
):
    """Verify WhatsApp webhook ownership with Meta."""
    expected_token = settings.META_WHATSAPP_APP_SECRET
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook")
async def receive_message(request: Request):
    """Receive and validate incoming WhatsApp messages."""
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()

    expected_signature = (
        "sha256="
        + hmac.new(
            settings.META_WHATSAPP_APP_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
    )

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        payload = await request.json()
        webhook = WhatsAppWebhook(**payload)
    except Exception as exc:
        logger.error(f"Invalid WhatsApp payload: {exc}")
        return {"status": "ignored"}

    for entry in webhook.entry:
        for change in entry.changes:
            if change.get("field") == "messages":
                logger.info("WhatsApp message event received")

    return {"status": "ok"}
