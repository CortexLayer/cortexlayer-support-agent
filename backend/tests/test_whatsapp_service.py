"""Tests for WhatsApp message processing service."""

import pytest

from backend.app.services.whatsapp_service import process_whatsapp_message


@pytest.mark.asyncio
async def test_process_whatsapp_text_message(monkeypatch):
    """Ensure text messages are processed without crashing."""

    async def fake_rag_pipeline(*args, **kwargs):
        return {
            "answer": "Test answer",
            "confidence": 0.9,
            "latency_ms": 10,
        }

    monkeypatch.setattr(
        "backend.app.services.whatsapp_service.run_rag_pipeline",
        fake_rag_pipeline,
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
    """Ensure non-text messages are ignored."""
    payload = {
        "messages": [
            {
                "from": "1234567890",
                "type": "image",
            }
        ]
    }

    await process_whatsapp_message(payload)
