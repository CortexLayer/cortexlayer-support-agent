"""Handoff ticket creation and escalation logic."""

from sqlalchemy.orm import Session
from backend.app.models.handoff import HandoffTicket, HandoffStatus
from backend.app.utils.logger import logger
from typing import Dict
from datetime import datetime


def create_handoff_ticket(
    client_id: str,
    query: str,
    context: str,
    db: Session
) -> HandoffTicket:
    """
    Create an escalation ticket when AI confidence is low
    """

    ticket = HandoffTicket(
        client_id=client_id,
        query_text=query,
        context=context,
        status=HandoffStatus.OPEN
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    logger.info(f"Created handoff ticket {ticket.id}")

    return ticket


def should_escalate(confidence: float, threshold: float = 0.3) -> bool:
    """
    Decide if a query should be escalated to human support
    """
    return confidence < threshold

