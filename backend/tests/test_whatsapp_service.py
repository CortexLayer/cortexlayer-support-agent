"""Tests for WhatsApp service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services.whatsapp_service import process_whatsapp_message


@pytest.mark.asyncio
async def test_process_whatsapp_text_message(monkeypatch):
    """Text WhatsApp messages are processed without crashing."""
    fake_db = MagicMock()
    fake_client = MagicMock()
    fake_client.is_disabled = False
    fake_client.plan_type.value = "growth"
    fake_client.id = "test-client-id"

    fake_db.query().filter().first.return_value = fake_client

    monkeypatch.setattr(
        "backend.app.services.whatsapp_service.SessionLocal",
        lambda: fake_db,
    )

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


@pytest.mark.asyncio
async def test_ignore_non_text_message():
    """Non-text WhatsApp messages are ignored."""
    payload = {
        "messages": [
            {
                "from": "1234567890",
                "type": "image",
            }
        ]
    }

    await process_whatsapp_message(payload)
