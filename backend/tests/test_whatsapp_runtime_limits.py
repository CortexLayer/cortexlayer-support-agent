"""Test WhatsApp runtime limits."""

import pytest

from backend.app.models.client import Client, PlanType
from backend.app.services.whatsapp_service import process_whatsapp_message


@pytest.mark.asyncio
async def test_starter_plan_whatsapp_blocked_runtime(db):
    """Test that starter plan WhatsApp messages are blocked at runtime."""
    client = Client(
        email="starter_runtime@test.com",
        hashed_password="x",
        company_name="TestCo",
        plan_type=PlanType.STARTER,
        is_disabled=False,
    )
    db.add(client)
    db.commit()

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
