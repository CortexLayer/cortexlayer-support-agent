"""Tests for WhatsApp webhook verification and security."""

import hashlib
import hmac

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app

client = TestClient(app)


def test_webhook_verification_success():
    """Webhook verification succeeds with correct token."""
    response = client.get(
        "/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "1234",
            "hub.verify_token": settings.META_WHATSAPP_APP_SECRET,
        },
    )

    assert response.status_code == 200
    assert response.text == "1234"


def test_webhook_verification_failure():
    """Webhook verification fails with incorrect token."""
    response = client.get(
        "/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "1234",
            "hub.verify_token": "wrong-token",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Webhook verification failed"


def test_webhook_post_invalid_signature():
    """POST webhook rejects invalid signature."""
    response = client.post(
        "/whatsapp/webhook",
        headers={"X-Hub-Signature-256": "sha256=fake"},
        json={},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid webhook signature"


def test_webhook_post_valid_signature_but_invalid_payload():
    """Valid signature but malformed payload is ignored safely."""
    body = b"{}"

    signature = (
        "sha256="
        + hmac.new(
            settings.META_WHATSAPP_APP_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
    )

    response = client.post(
        "/whatsapp/webhook",
        headers={"X-Hub-Signature-256": signature},
        content=body,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
