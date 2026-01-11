"""Tests for grace period enforcement."""

import uuid
from datetime import datetime, timedelta

from backend.app.models.client import BillingStatus, Client
from backend.app.services.grace import enforce_grace_period
import pytest
pytestmark = pytest.mark.integration


def test_grace_period_disables_old_clients(db) -> None:
    """Clients in grace > 7 days should become disabled."""
    old_time = datetime.utcnow() - timedelta(days=8)

    client = Client(
        id=uuid.uuid4(),
        email="grace@test.com",
        hashed_password="x",
        company_name="TestCo",
        billing_status=BillingStatus.GRACE_PERIOD,
        updated_at=old_time,
    )
    db.add(client)
    db.commit()

    enforce_grace_period(db)
    db.refresh(client)

    assert client.billing_status == BillingStatus.DISABLED
    assert client.is_disabled
