"""Analytics service for admin and internal usage.

This module provides read-only aggregation functions that summarize
usage, cost, and performance metrics for a given client.
"""

from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.chat_logs import ChatLog
from backend.app.models.documents import Document
from backend.app.models.usage import UsageLog


def get_cost_analytics(
    client_id: str,
    db: Session,
    days: int = 30,
) -> Dict:
    """Cost analytics for a client.

    - Daily cost trend
    - Cost grouped by model
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Daily cost trend
    daily_costs = (
        db.query(
            func.date(UsageLog.timestamp).label("date"),
            func.sum(UsageLog.cost_usd).label("cost"),
        )
        .filter(
            UsageLog.client_id == client_id,
            UsageLog.timestamp >= since,
        )
        .group_by(func.date(UsageLog.timestamp))
        .order_by(func.date(UsageLog.timestamp))
        .all()
    )

    # Cost by model
    cost_by_model = (
        db.query(
            UsageLog.model_used.label("model"),
            func.sum(UsageLog.cost_usd).label("cost"),
        )
        .filter(
            UsageLog.client_id == client_id,
            UsageLog.timestamp >= since,
        )
        .group_by(UsageLog.model_used)
        .order_by(func.sum(UsageLog.cost_usd).desc())
        .all()
    )

    return {
        "period_days": days,
        "daily_costs": [
            {
                "date": str(row.date),
                "cost_usd": float(row.cost or 0),
            }
            for row in daily_costs
        ],
        "cost_by_model": [
            {
                "model": row.model or "unknown",
                "cost_usd": float(row.cost or 0),
            }
            for row in cost_by_model
        ],
    }


def get_usage_summary(
    client_id: str,
    db: Session,
    days: int = 30,
) -> Dict[str, object]:
    """Get aggregated usage statistics for a client.

    Args:
        client_id: UUID of the client.
        db: Database session.
        days: Number of days to look back.

    Returns:
        Aggregated usage metrics.
    """
    since: datetime = datetime.utcnow() - timedelta(days=days)

    total_tokens_expr = (
        (UsageLog.input_tokens) + (UsageLog.output_tokens) + (UsageLog.embedding_tokens)
    )

    usage_rows = (
        db.query(
            UsageLog.operation_type.label("operation"),
            func.count(UsageLog.id).label("count"),
            func.sum(UsageLog.cost_usd).label("total_cost"),
            func.sum(total_tokens_expr).label("total_tokens"),
        )
        .filter(
            UsageLog.client_id == client_id,
            UsageLog.timestamp >= since,
        )
        .group_by(UsageLog.operation_type)
        .all()
    )

    conversation_count: int = (
        db.query(func.count(ChatLog.id))
        .filter(
            ChatLog.client_id == client_id,
            ChatLog.timestamp >= since,
        )
        .scalar()
        or 0
    )

    document_count: int = (
        db.query(func.count(Document.id))
        .filter(
            Document.client_id == client_id,
        )
        .scalar()
        or 0
    )

    usage_by_type: List[Dict[str, object]] = [
        {
            "operation": row.operation,
            "count": int(row.count),
            "cost_usd": float(row.total_cost or 0.0),
            "tokens": int(row.total_tokens or 0),
        }
        for row in usage_rows
    ]

    total_cost: float = sum(item["cost_usd"] for item in usage_by_type)

    return {
        "period_days": days,
        "total_conversations": conversation_count,
        "total_documents": document_count,
        "usage_by_type": usage_by_type,
        "total_cost_usd": round(total_cost, 4),
    }


def get_query_analytics(
    client_id: str,
    db: Session,
) -> Dict[str, float]:
    """Get query performance analytics for a client.

    Args:
        client_id: UUID of the client.
        db: Database session.

    Returns:
        Query performance metrics.
    """
    avg_latency: float = (
        db.query(
            func.avg(ChatLog.latency_ms),
        )
        .filter(
            ChatLog.client_id == client_id,
        )
        .scalar()
        or 0.0
    )

    avg_confidence: float = (
        db.query(
            func.avg(ChatLog.confidence_score),
        )
        .filter(
            ChatLog.client_id == client_id,
        )
        .scalar()
        or 0.0
    )

    return {
        "avg_latency_ms": round(avg_latency, 2),
        "avg_confidence": round(avg_confidence, 4),
    }
