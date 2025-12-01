"""Tests for overage billing logic."""

import uuid
from datetime import datetime

from backend.app.models.client import BillingStatus, Client, PlanType
from backend.app.models.usage import UsageLog
from backend.app.services.overage import check_and_bill_overages
from backend.tests.utils.mock_stripe import mock_stripe_success


def test_overage_soft_cap_creates_invoice(db, monkeypatch) -> None:
    """Soft cap exceed -> invoice item should be created."""
    stripe_mock = mock_stripe_success(monkeypatch)

    client = Client(
        id=uuid.uuid4(),
        email="overage@test.com",
        hashed_password="x",
        company_name="TestCo",
        plan_type=PlanType.STARTER,
        stripe_customer_id="cus_test123",
    )
    db.add(client)
    db.commit()

    # Exceed soft cap: starter limit=1000 -> soft cap=1200
    for _ in range(1300):
        log = UsageLog(
            client_id=client.id,
            operation_type="query",
            timestamp=datetime.utcnow(),
        )
        db.add(log)
    db.commit()

    check_and_bill_overages(client, db)

    stripe_mock.InvoiceItem.create.assert_called_once()


def test_overage_hard_cap_disables_client(db, monkeypatch) -> None:
    """Hard cap exceed -> client should be disabled."""
    mock_stripe_success(monkeypatch)

    client = Client(
        id=uuid.uuid4(),
        email="hardcap@test.com",
        hashed_password="x",
        company_name="TestCo",
        plan_type=PlanType.STARTER,
        billing_status=BillingStatus.ACTIVE,
    )
    db.add(client)
    db.commit()

    # Hard cap starter=1000 → 1500 queries threshold
    for _ in range(1600):
        db.add(
            UsageLog(
                client_id=client.id,
                operation_type="query",
                timestamp=datetime.utcnow(),
            )
        )
    db.commit()

    check_and_bill_overages(client, db)
    db.refresh(client)

    assert client.billing_status == BillingStatus.DISABLED
    assert client.is_disabled is True
