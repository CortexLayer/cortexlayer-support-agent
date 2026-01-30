"""Admin-facing API routes."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.dependencies.admin_auth import require_admin
from backend.app.models.chat_logs import ChatLog
from backend.app.models.client import Client
from backend.app.models.handoff import HandoffStatus, HandoffTicket
from backend.app.schemas.client import ClientResponse
from backend.app.services.analytics import (
    get_cost_analytics,
    get_document_analytics,
    get_query_analytics,
    get_usage_summary,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/clients", response_model=list[ClientResponse])
def list_clients(db: Session = Depends(get_db)):
    """List all clients."""
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
    """Get client details."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("/analytics/usage/{client_id}")
def get_client_usage_analytics(
    client_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Force eager settings validation at application startup."""
    return get_usage_summary(str(client_id), db, days)


@router.get("/analytics/cost/{client_id}")
def get_client_cost_analytics(
    client_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Return Client's cost analytics."""
    return get_cost_analytics(str(client_id), db, days)


@router.get("/analytics/query/{client_id}")
def get_client_query_analytics(
    client_id: UUID,
    db: Session = Depends(get_db),
):
    """Return Client's query analytics."""
    return get_query_analytics(str(client_id), db)


@router.get("/analytics/documents/{client_id}")
def get_client_document_analytics(
    client_id: UUID,
    db: Session = Depends(get_db),
):
    """Return Client's documents analytics."""
    return get_document_analytics(str(client_id), db)


@router.get("/dashboard/{client_id}")
def get_client_dashboard(
    client_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Provides the client dash."""
    cid = str(client_id)
    return {
        "usage": get_usage_summary(cid, db, days),
        "costs": get_cost_analytics(cid, db, days),
        "documents": get_document_analytics(cid, db),
        "queries": get_query_analytics(cid, db),
    }


@router.get("/analytics/whatsapp/messages")
def whatsapp_message_analytics(db: Session = Depends(get_db)):
    """Provide whatsapp messages analytics."""
    total = db.query(ChatLog).filter(ChatLog.channel == "whatsapp").count()

    per_client = (
        db.query(Client.company_name, func.count(ChatLog.id))
        .join(ChatLog, ChatLog.client_id == Client.id)
        .filter(ChatLog.channel == "whatsapp")
        .group_by(Client.company_name)
        .order_by(func.count(ChatLog.id).desc())
        .all()
    )

    return {
        "total_messages": total,
        "messages_per_client": [
            {"company": name, "message_count": count} for name, count in per_client
        ],
    }


@router.get("/analytics/whatsapp/performance")
def whatsapp_performance_analytics(db: Session = Depends(get_db)):
    """Provide whatsapp performance analytics."""
    avg_lat, min_lat, max_lat = (
        db.query(
            func.avg(ChatLog.latency_ms),
            func.min(ChatLog.latency_ms),
            func.max(ChatLog.latency_ms),
        )
        .filter(ChatLog.channel == "whatsapp")
        .first()
    )

    return {
        "average_latency_ms": int(avg_lat) if avg_lat else 0,
        "min_latency_ms": min_lat or 0,
        "max_latency_ms": max_lat or 0,
    }


@router.get("/analytics/whatsapp/activity")
def whatsapp_activity_analytics(db: Session = Depends(get_db)):
    """Provide whatsapp activity analytics."""
    dialect = db.bind.dialect.name

    hour_expr = (
        func.strftime("%H", ChatLog.timestamp)
        if dialect == "sqlite"
        else func.extract("hour", ChatLog.timestamp)
    )

    activity = (
        db.query(hour_expr.label("hour"), func.count(ChatLog.id))
        .filter(ChatLog.channel == "whatsapp")
        .group_by(hour_expr)
        .order_by(hour_expr)
        .all()
    )

    return {
        "activity_by_hour": [
            {"hour": int(hour), "message_count": count}
            for hour, count in activity
            if hour is not None
        ]
    }


@router.get("/handoff/list")
def list_handoff_tickets(
    status: Optional[HandoffStatus] = None,
    db: Session = Depends(get_db),
):
    """List handoff tickets."""
    query = db.query(HandoffTicket)
    if status:
        query = query.filter(HandoffTicket.status == status)

    tickets = query.order_by(HandoffTicket.created_at.desc()).all()
    return {"tickets": tickets}


@router.post("/handoff/{ticket_id}/resolve")
def resolve_handoff_ticket(ticket_id: UUID, db: Session = Depends(get_db)):
    """Mark a handoff ticket as resolved."""
    ticket = db.query(HandoffTicket).filter(HandoffTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = HandoffStatus.RESOLVED
    ticket.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return {"message": "Ticket resolved", "ticket_id": ticket.id}
