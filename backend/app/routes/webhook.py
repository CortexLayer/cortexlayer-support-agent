"""Stripe webhook handlers for subscription billing events."""

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.client import BillingStatus, Client
from backend.app.utils.logger import logger

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Validate and process Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payload") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid signature",
        ) from exc

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "invoice.paid":
        handle_invoice_paid(data, db)
    elif event_type == "invoice.payment_failed":
        handle_payment_failed(data, db)
    elif event_type == "customer.subscription.deleted":
        handle_subscription_deleted(data, db)

    return {"status": "success"}


def extract_customer_id(obj: dict) -> str | None:
    """Extract a Stripe customer ID from different event formats."""
    return (
        obj.get("customer")
        or obj.get("customer_id")
        or (obj.get("customer_details") or {}).get("id")
        or None
    )


def handle_invoice_paid(invoice: dict, db: Session) -> None:
    """Handle invoice.paid events and activate the client."""
    customer_id = extract_customer_id(invoice)
    if not customer_id:
        return

    client = db.query(Client).filter(Client.stripe_customer_id == customer_id).first()
    if not client:
        return

    client.billing_status = BillingStatus.ACTIVE
    client.is_disabled = False
    db.commit()

    logger.info("Invoice paid: %s", client.email)


def handle_payment_failed(invoice: dict, db: Session) -> None:
    """Handle payment failure and start grace period."""
    customer_id = extract_customer_id(invoice)
    if not customer_id:
        return

    client = db.query(Client).filter(Client.stripe_customer_id == customer_id).first()
    if not client:
        return

    client.billing_status = BillingStatus.GRACE_PERIOD
    db.commit()

    logger.warning("Payment failed: %s", client.email)


def handle_subscription_deleted(subscription: dict, db: Session) -> None:
    """Handle subscription cancellation and disable account."""
    customer_id = extract_customer_id(subscription)
    if not customer_id:
        return

    client = db.query(Client).filter(Client.stripe_customer_id == customer_id).first()
    if not client:
        return

    client.billing_status = BillingStatus.DISABLED
    client.is_disabled = True
    db.commit()

    logger.info("Subscription cancelled: %s", client.email)
