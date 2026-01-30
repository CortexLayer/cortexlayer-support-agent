"""Tests for admin handoff ticket workflows."""

import uuid

from backend.app.models.client import Client
from backend.app.models.handoff import HandoffStatus
from backend.app.services.handoff_service import create_handoff_ticket


def test_list_handoff_tickets(client, admin_headers):
    """Ensure admin can list handoff tickets."""
    response = client.get(
        "/admin/handoff/list",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert "tickets" in response.json()


def test_resolve_handoff_ticket(client, db, admin_headers):
    """Ensure admin can resolve handoff tickets."""
    # Create client
    c = Client(
        id=uuid.uuid4(),
        email="admin@test.com",
        hashed_password="x",
        company_name="Admin Test",
    )
    db.add(c)
    db.commit()

    # Create ticket
    ticket = create_handoff_ticket(
        client_id=c.id,
        query="Help me",
        context="Low confidence",
        db=db,
    )

    # Resolve
    response = client.post(f"/admin/handoff/{ticket.id}/resolve", headers=admin_headers)
    assert response.status_code == 200

    db.refresh(ticket)
    assert ticket.status == HandoffStatus.RESOLVED
    assert ticket.resolved_at is not None
