"""Tests for Stripe customer & subscription helpers."""

from backend.app.services.stripe_service import (
    cancel_subscription,
    create_customer,
    create_subscription,
)
from backend.tests.utils.mock_stripe import mock_stripe_success


def test_create_customer(monkeypatch) -> None:
    """Stripe customer creation should succeed."""
    stripe_mock = mock_stripe_success(monkeypatch)

    cid = create_customer("x@test.com", "Test User")
    assert cid == "cus_test123"
    stripe_mock.Customer.create.assert_called_once()


def test_create_subscription(monkeypatch) -> None:
    """Subscription creation should return subscription_id and secret."""
    stripe_mock = mock_stripe_success(monkeypatch)

    result = create_subscription("cus_test123", "price_test")
    assert result["subscription_id"] == "sub_test123"
    assert result["client_secret"] == "pi_secret_test"

    stripe_mock.Subscription.create.assert_called_once()


def test_cancel_subscription(monkeypatch) -> None:
    """Subscription cancellation should call Stripe delete."""
    stripe_mock = mock_stripe_success(monkeypatch)

    cancel_subscription("sub_test123")
    stripe_mock.Subscription.delete.assert_called_once()
