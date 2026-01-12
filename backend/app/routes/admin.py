"""Admin-facing API routes.

These endpoints provide read-only access to client data and
aggregated usage, cost, and performance analytics for
administrative and operational purposes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.models.client import Client
from backend.app.schemas.client import ClientResponse
from backend.app.services.analytics import (
    get_cost_analytics,
    get_document_analytics,
    get_query_analytics,
    get_usage_summary,
)


from typing import Optional, List
from datetime import datetime


from backend.app.models.handoff import HandoffTicket, HandoffStatus

router = APIRouter(prefix="/admin", tags=["Admin"])

# Client Management


@router.get("/clients", response_model=list[ClientResponse])
def list_clients(db: Session = Depends(get_db)):
    """Return a list of all registered clients."""
    return (
        db.query(Client)
        .options(
            joinedload(Client.documents),
            joinedload(Client.usage_logs),
        )
        .all()
    )


@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(client_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a single client by its unique identifier."""
    client = db.query(Client).filter(Client.id == client_id).first()

    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    return client


# Analytics Endpoints


@router.get("/analytics/usage/{client_id}")
def get_client_usage_analytics(
    client_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Return aggregated usage analytics for a client."""
    return get_usage_summary(
        client_id=str(client_id),
        db=db,
        days=days,
    )


@router.get("/analytics/cost/{client_id}")
def get_client_cost_analytics(
    client_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Return cost analytics for a client.

    Includes:
    - Daily cost trend
    - Cost grouped by model
    """
    return get_cost_analytics(
        client_id=str(client_id),
        db=db,
        days=days,
    )


@router.get("/analytics/query/{client_id}")
def get_client_query_analytics(
    client_id: UUID,
    db: Session = Depends(get_db),
):
    """Return query performance analytics for a client.

    Includes:
    - Average latency
    - Average confidence score
    """
    return get_query_analytics(
        client_id=str(client_id),
        db=db,
    )


@router.get("/analytics/documents/{client_id}")
def get_client_document_analytics(
    client_id: UUID,
    db: Session = Depends(get_db),
):
    """Return document analytics for a client."""
    return get_document_analytics(
        client_id=str(client_id),
        db=db,
    )


@router.get("/dashboard/{client_id}")
def get_client_dashboard(
    client_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Unified admin dashboard endpoint.

    Returns usage, cost, document, and query analytics
    for a single client in one response.
    """
    client_id_str = str(client_id)

    return {
        "usage": get_usage_summary(
            client_id=client_id_str,
            db=db,
            days=days,
        ),
        "costs": get_cost_analytics(
            client_id=client_id_str,
            db=db,
            days=days,
        ),
        "documents": get_document_analytics(
            client_id=client_id_str,
            db=db,
        ),
        "queries": get_query_analytics(
            client_id=client_id_str,
            db=db,
        ),
    }

@router.get("/handoff/list")
def list_handoff_tickets(
    status: Optional[HandoffStatus] = None,
    db: Session = Depends(get_db),
):
    """
    List all handoff tickets.
    Optional filter by status.
    """
    query = db.query(HandoffTicket)

    if status:
        query = query.filter(HandoffTicket.status == status)

    tickets = query.order_by(HandoffTicket.created_at.desc()).all()

    return {"tickets": tickets}

@router.post("/handoff/{ticket_id}/resolve")
def resolve_handoff_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Resolve a handoff ticket.
    """
    ticket = db.query(HandoffTicket).filter(
        HandoffTicket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = HandoffStatus.RESOLVED
    ticket.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return {"message": "Ticket resolved", "ticket_id": ticket.id}


