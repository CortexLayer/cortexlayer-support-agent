"""Overage billing logic."""

from datetime import datetime

import stripe
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.client import BillingStatus, Client
from backend.app.models.usage import UsageLog
from backend.app.services.usage_limits import get_plan_limits
from backend.app.utils.logger import logger


def check_and_bill_overages(client: Client, db: Session) -> None:
    """Check if client exceeded plan usage and bill for overages."""
    limits = get_plan_limits(client.plan_type)

    start_of_month = datetime.utcnow().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    usage = (
        db.query(
            func.count(UsageLog.id).label("count"),
            func.sum(UsageLog.cost_usd).label("total_cost"),
        )
        .filter(
            UsageLog.client_id == client.id,
            UsageLog.timestamp >= start_of_month,
        )
        .first()
    )

    query_count = usage.count or 0
    plan_limit = limits["queries_per_month"]
    hard_cap = int(plan_limit * 1.5)

    if query_count > plan_limit:
        overage_queries = query_count - plan_limit
        overage_cost = overage_queries * 0.01

        try:
            stripe.InvoiceItem.create(
                customer=client.stripe_customer_id,
                amount=int(overage_cost * 100),
                currency="usd",
                description=(f"Overage: {overage_queries} queries"),
            )
            logger.info(
                "Billed $%.2f overage to %s",
                overage_cost,
                client.email,
            )
        except Exception as exc:
            logger.error("Overage billing failed: %s", exc)

    if query_count > hard_cap:
        client.billing_status = BillingStatus.DISABLED
        client.is_disabled = True
        db.commit()
        logger.warning(
            "Client %s disabled for exceeding hard cap.",
            client.email,
        )
