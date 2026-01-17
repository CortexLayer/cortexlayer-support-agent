"""Tests for WhatsApp usage limits."""

from datetime import datetime, timezone

from backend.app.models.usage import UsageLog
from backend.app.services.usage_limits import check_whatsapp_limit


def test_whatsapp_limit_exceeded(db_session):
    """Test that WhatsApp limit is enforced."""
    client_id = 1

    for _ in range(100):
        db_session.add(
            UsageLog(
                client_id=client_id,
                operation_type="whatsapp",
                created_at=datetime.now(timezone.utc),
            )
        )

    db_session.commit()

    allowed = check_whatsapp_limit(
        db=db_session,
        client_id=client_id,
        plan_type="growth",
    )

    assert allowed is False


def test_whatsapp_limit_allows_when_under_limit(db_session):
    """Test that WhatsApp limit is allowed when under limit."""
    client_id = 2

    db_session.add(
        UsageLog(
            client_id=client_id,
            operation_type="whatsapp",
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    allowed = check_whatsapp_limit(
        db=db_session,
        client_id=client_id,
        plan_type="growth",
    )

    assert allowed is True
