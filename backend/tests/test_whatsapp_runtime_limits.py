"""Supported external contact channels for clients."""

import uuid

import pytest

from backend.app.models.client import Client, PlanType
from backend.app.models.client_contact import ClientContact
from backend.app.services.whatsapp_service import process_whatsapp_message


@pytest.mark.asyncio
async def test_starter_plan_whatsapp_blocked_runtime(db, monkeypatch):
    """Starter plan WhatsApp messages are blocked at runtime."""
    client = Client(
        id=uuid.uuid4(),
        email="starter_runtime@test.com",
        hashed_password="x",
        company_name="TestCo",
        plan_type=PlanType.STARTER,
        is_disabled=False,
    )
    db.add(client)
    db.commit()

    db.add(
        ClientContact(
            client_id=client.id,
            channel="whatsapp",
            external_id="123",
        )
    )
    db.commit()

    monkeypatch.setattr(
        "backend.app.services.whatsapp_service.send_whatsapp_message",
        lambda *args, **kwargs: None,
    )

    payload = {
        "messages": [
            {
                "from": "123",
                "type": "text",
                "text": {"body": "Hello"},
            }
        ]
    }

    await process_whatsapp_message(payload)
