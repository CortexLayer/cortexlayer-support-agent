"""WhatsApp service processing tests."""

from unittest.mock import AsyncMock

import pytest

from backend.app.models.client import Client, PlanType
from backend.app.models.client_contact import ClientContact
from backend.app.services.whatsapp_service import process_whatsapp_message


@pytest.mark.asyncio
async def test_process_whatsapp_text_message(db, monkeypatch):
    """Text WhatsApp messages are processed and replied."""
    client = Client(
        email="growth@test.com",
        hashed_password="x",
        company_name="Growth Corp",
        plan_type=PlanType.GROWTH,
        is_disabled=False,
    )
    db.add(client)
    db.commit()

    db.add(
        ClientContact(
            client_id=client.id,
            channel="whatsapp",
            external_id="1234567890",
        )
    )
    db.commit()

    monkeypatch.setattr(
        "backend.app.services.whatsapp_service.run_rag_pipeline",
        AsyncMock(
            return_value={
                "answer": "Test answer",
                "confidence": 0.9,
                "latency_ms": 10,
                "usage_stats": {
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "cost_usd": 0.0,
                    "model_used": "test",
                },
            }
        ),
    )

    monkeypatch.setattr(
        "backend.app.services.whatsapp_service.send_whatsapp_message",
        AsyncMock(),
    )

    payload = {
        "messages": [
            {
                "from": "1234567890",
                "type": "text",
                "text": {"body": "Hello"},
            }
        ]
    }

    await process_whatsapp_message(payload)
