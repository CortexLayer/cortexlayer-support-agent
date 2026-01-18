"""Plan limits and enforcement utilities."""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.client import Client, PlanType
from backend.app.models.documents import Document
from backend.app.models.usage import UsageLog

PLAN_LIMITS = {
    PlanType.STARTER: {
        "max_docs": 10,
        "max_file_mb": 5,
        "max_chunks_per_doc": 250,
        "queries_per_month": 1000,
        "rate_limit_per_min": 15,
        "whatsapp_messages": 0,
    },
    PlanType.GROWTH: {
        "max_docs": 50,
        "max_file_mb": 10,
        "max_chunks_per_doc": 500,
        "queries_per_month": 5000,
        "rate_limit_per_min": 50,
        "whatsapp_messages": 2000,
    },
    PlanType.SCALE: {
        "max_docs": 1000,
        "max_file_mb": 20,
        "max_chunks_per_doc": 3000,
        "queries_per_month": 50000,
        "rate_limit_per_min": 100,
        "whatsapp_messages": 10000,
    },
}


def get_plan_limits(plan_type: PlanType) -> dict:
    """Return plan limit values for a given plan."""
    return PLAN_LIMITS.get(plan_type, PLAN_LIMITS[PlanType.STARTER])


def check_query_limit(client: Client, db: Session) -> bool:
    """Ensure client has not exceeded monthly query usage."""
    limits = get_plan_limits(client.plan_type)

    start = datetime.utcnow().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    used_queries = (
        db.query(func.count(UsageLog.id))
        .filter(
            UsageLog.client_id == client.id,
            UsageLog.operation_type == "query",
            UsageLog.timestamp >= start,
        )
        .scalar()
    )

    if used_queries >= limits["queries_per_month"]:
        raise HTTPException(
            status_code=429,
            detail=f"You have used all {limits['queries_per_month']} monthly queries.",
        )

    return True


def check_document_limit(client: Client, db: Session) -> bool:
    """Ensure client stays within allowed document count."""
    limits = get_plan_limits(client.plan_type)

    doc_count = (
        db.query(func.count(Document.id))
        .filter(
            Document.client_id == client.id,
        )
        .scalar()
    )

    if doc_count >= limits["max_docs"]:
        raise HTTPException(
            status_code=403,
            detail=f"Document limit reached ({limits['max_docs']}).",
        )

    return True


def check_file_size(file_size_bytes: int, plan_type: PlanType) -> bool:
    """Validate file upload size against plan limits."""
    limits = get_plan_limits(plan_type)
    max_bytes = limits["max_file_mb"] * 1024 * 1024

    if file_size_bytes > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (>{limits['max_file_mb']} MB).",
        )

    return True


def check_whatsapp_limit(client: Client, db: Session) -> bool:
    """Ensure client has not exceeded monthly WhatsApp message usage."""
    limits = get_plan_limits(client.plan_type)

    max_messages = limits.get("whatsapp_messages", 0)
    if max_messages == 0:
        raise HTTPException(
            status_code=403,
            detail="WhatsApp support is not available on your plan.",
        )

    start = datetime.utcnow().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    used_messages = (
        db.query(func.count(UsageLog.id))
        .filter(
            UsageLog.client_id == client.id,
            UsageLog.operation_type == "whatsapp",
            UsageLog.timestamp >= start,
        )
        .scalar()
    )

    if used_messages >= max_messages:
        raise HTTPException(
            status_code=429,
            detail="Monthly WhatsApp message limit exceeded.",
        )

    return True
