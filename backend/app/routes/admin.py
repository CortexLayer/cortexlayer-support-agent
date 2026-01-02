"""Admin-facing API routes.

These endpoints provide read-only access to client data and
aggregated usage analytics for administrative and operational purposes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.models.client import Client
from backend.app.schemas.client import ClientResponse
from backend.app.services.analytics import get_usage_summary

router = APIRouter(prefix="/admin", tags=["Admin"])


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


@router.get(
    "/clients/{client_id}",
    response_model=ClientResponse,
)
def get_client(client_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a single client by its unique identifier.

    Args:
        client_id: UUID of the client.
        db: Database session dependency.

    Raises:
        HTTPException: If the client does not exist.

    Returns:
        The requested client record.
    """
    client = db.query(Client).filter(Client.id == client_id).first()

    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    return client


@router.get("/analytics/usage/{client_id}")
def get_client_usage_analytics(
    client_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Return aggregated usage analytics for a client.

    This endpoint summarizes usage logs, cost, token consumption,
    conversation volume, and document counts for a given client.

    Args:
        client_id: UUID of the client.
        days: Number of days to look back for analytics.
        db: Database session dependency.

    Returns:
        Aggregated usage analytics data.
    """
    return get_usage_summary(
        client_id=str(client_id),
        db=db,
        days=days,
    )
