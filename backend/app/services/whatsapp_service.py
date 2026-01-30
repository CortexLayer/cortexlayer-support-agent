"""WhatsApp message processing service."""

from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.chat_logs import ChatLog
from backend.app.models.client_contact import ClientContact
from backend.app.models.usage import UsageLog
from backend.app.rag.pipeline import run_rag_pipeline
from backend.app.services.usage_limits import check_whatsapp_limit
from backend.app.services.whatsapp_sender import send_whatsapp_message
from backend.app.utils.logger import logger


async def process_whatsapp_message(payload: Dict) -> None:
    """Process a WhatsApp webhook payload safely."""
    messages = payload.get("messages", [])
    if not messages:
        return

    message = messages[0]
    if message.get("type") != "text":
        return

    from_number = message.get("from")
    text = message.get("text", {}).get("body", "").strip()

    if not text:
        return

    db: Session = SessionLocal()

    try:
        contact = (
            db.query(ClientContact)
            .filter(
                ClientContact.channel == "whatsapp",
                ClientContact.external_id == from_number,
            )
            .one_or_none()
        )

        if not contact:
            logger.warning(
                "WhatsApp message from unknown number",
                extra={"from": from_number},
            )
            return

        client = contact.client

        # Enforce limits BEFORE RAG
        check_whatsapp_limit(client, db)

        result = await run_rag_pipeline(
            client_id=str(client.id),
            query=text,
            plan_type=client.plan_type.value,
        )

        # Persist chat
        db.add(
            ChatLog(
                client_id=client.id,
                query_text=text,
                response_text=result["answer"],
                confidence_score=result["confidence"],
                latency_ms=result["latency_ms"],
                channel="whatsapp",
            )
        )

        # Persist usage
        usage = result["usage_stats"]
        db.add(
            UsageLog(
                client_id=client.id,
                operation_type="whatsapp",
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                cost_usd=usage["cost_usd"],
                model_used=usage["model_used"],
                latency_ms=result["latency_ms"],
                timestamp=datetime.utcnow(),
            )
        )

        db.commit()

        # Send reply
        await send_whatsapp_message(
            to_number=from_number,
            message=result["answer"],
        )

    except Exception as exc:
        db.rollback()
        logger.error("WhatsApp processing failed: %s", exc)

    finally:
        db.close()
