"""Stripe integration service.

Customer creation, Subscription creation, Subscription cancellation.
"""

import stripe

from backend.app.core.config import settings
from backend.app.utils.logger import logger

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_customer(email: str, name: str) -> str:
    """Create a Stripe customer and return the customer ID."""
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"source": "cortexlayer"},
        )
        logger.info(f"Stripe customer created: {customer.id}")
        return customer.id
    except stripe.error.StripeError as exc:
        logger.error(f"Stripe customer creation failed: {exc}")
        raise


def create_subscription(customer_id: str, price_id: str) -> dict:
    """Create a subscription for a given customer.

    Returns subscription_id + client_secret (for frontend payment flow).
    """
    try:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )

        logger.info(f"Stripe subscription created: {subscription.id}")

        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret,
        }

    except stripe.error.StripeError as exc:
        logger.error(f"Subscription creation failed: {exc}")
        raise


def cancel_subscription(subscription_id: str) -> None:
    """Cancel an active subscription."""
    try:
        stripe.Subscription.delete(subscription_id)
        logger.info(f"Stripe subscription cancelled: {subscription_id}")
    except stripe.error.StripeError as exc:
        logger.error(f"Subscription cancellation failed: {exc}")
        raise
