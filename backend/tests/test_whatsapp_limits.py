"""Tests for WhatsApp usage limits."""

import uuid
from datetime import datetime

import pytest
from fastapi import HTTPException

from backend.app.models.client import Client, PlanType
from backend.app.models.usage import UsageLog
from backend.app.services.usage_limits import check_whatsapp_limit


def test_starter_plan_whatsapp_blocked(db):
    """Starter plan must not allow WhatsApp usage."""
    client = Client(
        email="starter@test.com",
        hashed_password="x",
        company_name="Starter Corp",
        plan_type=PlanType.STARTER,
        is_disabled=False,
    )
    db.add(client)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        check_whatsapp_limit(client, db)

    assert exc.value.status_code == 403


def test_growth_plan_whatsapp_allowed_when_empty(db):
    """Growth plan allows WhatsApp when no usage exists."""
    client = Client(
        email="growth@test.com",
        hashed_password="x",
        company_name="Growth Corp",
        plan_type=PlanType.GROWTH,
        is_disabled=False,
    )
    db.add(client)
    db.commit()

    assert check_whatsapp_limit(client, db) is True


def test_whatsapp_limit_exceeded(db):
    """Growth plan blocked after exceeding WhatsApp limit."""
    client = Client(
        email=f"limit-{uuid.uuid4()}@test.com",
        hashed_password="x",
        company_name="Limit Corp",
        plan_type=PlanType.GROWTH,
        is_disabled=False,
    )
    db.add(client)
    db.commit()

    for _ in range(2000):
        db.add(
            UsageLog(
                client_id=client.id,
                operation_type="whatsapp",
                timestamp=datetime.utcnow(),
            )
        )

    db.commit()

    with pytest.raises(HTTPException):
        check_whatsapp_limit(client, db)
