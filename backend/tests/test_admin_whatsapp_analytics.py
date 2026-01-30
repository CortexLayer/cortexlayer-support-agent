"""Test WhatsApp analytics."""

import uuid
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.chat_logs import ChatLog
from backend.app.models.client import Client


def seed_whatsapp_logs(db: Session):
    """Seed WhatsApp logs for testing."""
    client = Client(
        id=uuid.uuid4(),
        email=f"admin_{uuid.uuid4()}@test.com",
        hashed_password="x",
        company_name="Test Corp",
    )
    db.add(client)
    db.commit()

    logs = [
        ChatLog(
            client_id=client.id,
            query_text="Hello",
            response_text="Hi",
            channel="whatsapp",
            latency_ms=300,
            timestamp=datetime.utcnow(),
        ),
        ChatLog(
            client_id=client.id,
            query_text="Help",
            response_text="Sure",
            channel="whatsapp",
            latency_ms=500,
            timestamp=datetime.utcnow(),
        ),
    ]

    db.add_all(logs)
    db.commit()


def test_whatsapp_message_analytics(client: TestClient, db: Session, admin_headers):
    """Test WhatsApp message analytics."""
    seed_whatsapp_logs(db)

    response = client.get("/admin/analytics/whatsapp/messages", headers=admin_headers)
    assert response.status_code == 200

    data = response.json()
    assert "total_messages" in data
    assert "messages_per_client" in data
    assert data["total_messages"] >= 2


def test_whatsapp_performance_analytics(client: TestClient, db: Session, admin_headers):
    """Test WhatsApp performance analytics."""
    seed_whatsapp_logs(db)

    response = client.get(
        "/admin/analytics/whatsapp/performance",
        headers=admin_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "average_latency_ms" in data
    assert data["average_latency_ms"] > 0


def test_whatsapp_activity_analytics(client: TestClient, db: Session, admin_headers):
    """Test WhatsApp activity analytics."""
    seed_whatsapp_logs(db)

    response = client.get("/admin/analytics/whatsapp/activity", headers=admin_headers)
    assert response.status_code == 200

    data = response.json()
    assert "activity_by_hour" in data
    assert isinstance(data["activity_by_hour"], list)
