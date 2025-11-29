"""Daily scheduled jobs."""

from sqlalchemy.orm import Session

from backend.app.models.client import Client
from backend.app.services.grace import enforce_grace_period
from backend.app.services.overage import check_and_bill_overages


def run_daily_jobs(db: Session) -> None:
    """Run daily overage billing and grace period cleanup."""
    clients = db.query(Client).all()

    for client in clients:
        check_and_bill_overages(client, db)

    enforce_grace_period(db)
