"""Tests for Stripe webhook router."""

import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

pytestmark = pytest.mark.integration


def test_webhook_invoice_paid(monkeypatch, db) -> None:
    """invoice.paid should trigger handler and update client."""
    # Prepare fake client in DB
    import uuid

    from backend.app.models.client import BillingStatus, Client

    client = Client(
        id=uuid.uuid4(),
        email="webhook@test.com",
        hashed_password="x",
        company_name="TC",
        stripe_customer_id="cus_1234",
    )
    db.add(client)
    db.commit()

    # Mock signature verification
    mock_construct = MagicMock()
    event = {
        "type": "invoice.paid",
        "data": {"object": {"customer": "cus_1234"}},
    }
    mock_construct.return_value = event

    monkeypatch.setattr(
        "backend.app.routes.webhook.stripe.Webhook.construct_event",
        mock_construct,
    )

    client_api = TestClient(app, base_url="http://localhost")
    response = client_api.post(
        "/webhook/stripe",
        data=json.dumps(event),  # payload doesn't matter; we mock construct_event
        headers={"stripe-signature": "test"},
    )

    assert response.status_code == 200

    db.refresh(client)
    assert client.billing_status == BillingStatus.ACTIVE
    assert client.is_disabled is False
