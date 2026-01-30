"""Overage billing and enforcement logic."""

from datetime import datetime

import stripe
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.client import BillingStatus, Client
from backend.app.models.usage import UsageLog
from backend.app.services.usage_limits import get_plan_limits
from backend.app.utils.logger import logger


def check_and_bill_overages(client: Client, db: Session) -> None:
    """Evaluate monthly query usage and enforce billing rules.

    No commits performed here.
    """
    limits = get_plan_limits(client.plan_type)

    start_of_month = datetime.utcnow().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    query_count = (
        db.query(func.count(UsageLog.id))
        .filter(
            UsageLog.client_id == client.id,
            UsageLog.operation_type == "query",
            UsageLog.timestamp >= start_of_month,
        )
        .scalar()
        or 0
    )

    plan_limit = limits["queries_per_month"]
    hard_cap = int(plan_limit * 1.5)

    # Soft cap → invoice
    if query_count > plan_limit:
        overage_queries = query_count - plan_limit
        overage_cost_usd = overage_queries * 0.01

        try:
            stripe.InvoiceItem.create(
                customer=client.stripe_customer_id,
                amount=int(overage_cost_usd * 100),
                currency="usd",
                description=f"Query overage: {overage_queries} queries",
            )
            logger.info(
                "Overage billed | client=%s | queries=%s | $%.2f",
                client.email,
                overage_queries,
                overage_cost_usd,
            )
        except Exception as exc:
            logger.error(
                "Stripe overage billing failed for %s: %s",
                client.email,
                exc,
            )
            client.billing_status = BillingStatus.GRACE_PERIOD

    # Hard cap → disable
    if query_count > hard_cap:
        client.billing_status = BillingStatus.DISABLED
        client.is_disabled = True
        logger.warning(
            "Client disabled for hard cap exceed | %s",
            client.email,
        )
