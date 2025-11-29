"""Grace period enforcement logic."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.models.client import BillingStatus, Client
from backend.app.utils.logger import logger


def enforce_grace_period(db: Session) -> None:
    """Disable clients who stayed in grace period for more than 7 days."""
    cutoff = datetime.utcnow() - timedelta(days=7)

    clients = (
        db.query(Client)
        .filter(
            Client.billing_status == BillingStatus.GRACE_PERIOD,
        )
        .all()
    )

    for client in clients:
        if client.updated_at < cutoff:
            client.billing_status = BillingStatus.DISABLED
            client.is_disabled = True
            db.commit()

            logger.warning(
                "Disabled client %s for exceeding grace period.",
                client.email,
            )
