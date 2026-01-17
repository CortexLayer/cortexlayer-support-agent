"""WhatsApp message processing service."""

from typing import Dict

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.chat_logs import ChatLog
from backend.app.models.client import Client
from backend.app.models.usage import UsageLog
from backend.app.rag.pipeline import run_rag_pipeline
from backend.app.services.usage_limits import check_whatsapp_limit
from backend.app.utils.logger import logger


async def process_whatsapp_message(webhook_value: Dict) -> None:
    """Process a WhatsApp webhook payload."""
    messages = webhook_value.get("messages", [])
    if not messages:
        logger.info("No messages found in webhook payload")
        return

    message = messages[0]
    if message.get("type") != "text":
        logger.info("Non-text WhatsApp message received, ignoring")
        return

    from_number = message.get("from")
    message_text = message.get("text", {}).get("body", "")

    if not message_text.strip():
        logger.info("Empty WhatsApp text message, ignoring")
        return

    logger.info(
        "WhatsApp message received",
        extra={"from": from_number, "text": message_text},
    )

    db: Session = SessionLocal()

    try:
        client = db.query(Client).filter(Client.is_disabled.is_(False)).first()
        if not client:
            logger.warning("No active client found for WhatsApp message")
            return

        check_whatsapp_limit(client, db)

        result = await run_rag_pipeline(
            client_id=str(client.id),
            query=message_text,
            plan_type=client.plan_type.value,
        )

        chat_log = ChatLog(
            client_id=client.id,
            query_text=message_text,
            response_text=result["answer"],
            confidence_score=result["confidence"],
            latency_ms=result["latency_ms"],
            channel="whatsapp",
        )
        db.add(chat_log)

        usage_log = UsageLog(
            client_id=client.id,
            operation_type="whatsapp",
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            model_used="rag",
        )
        db.add(usage_log)

        db.commit()

    except Exception as exc:
        logger.error(f"WhatsApp processing failed: {exc}")

    finally:
        db.close()
