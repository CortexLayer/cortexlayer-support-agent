"""Mocked Stripe API for isolated testing."""

from unittest.mock import MagicMock


def mock_stripe_success(monkeypatch):
    """Mock Stripe calls to always succeed in tests."""
    stripe_mock = MagicMock()

    stripe_mock.InvoiceItem.create.return_value = {
        "id": "ii_mocked_invoice_item",
        "amount": 100,
    }

    stripe_mock.Customer.create.return_value = MagicMock(id="cus_test123")

    stripe_mock.Subscription.create.return_value = MagicMock(
        id="sub_test123",
        latest_invoice=MagicMock(
            payment_intent=MagicMock(client_secret="pi_secret_test"),
        ),
    )

    stripe_mock.Subscription.delete.return_value = {"deleted": True}

    monkeypatch.setattr("backend.app.services.stripe_service.stripe", stripe_mock)
    monkeypatch.setattr("backend.app.services.overage.stripe", stripe_mock)

    return stripe_mock
