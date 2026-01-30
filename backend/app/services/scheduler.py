"""Daily scheduled jobs for billing and account enforcement.

This module is intended to be executed by cron or a scheduler container.
"""

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.client import Client
from backend.app.services.grace import enforce_grace_period
from backend.app.services.overage import check_and_bill_overages
from backend.app.utils.logger import logger


def run_daily_jobs(db: Session) -> None:
    """Run daily overage billing and grace period cleanup.

    This function assumes ownership of the provided DB session.
    """
    clients = db.query(Client).all()

    for client in clients:
        try:
            check_and_bill_overages(client, db)
        except Exception as exc:
            logger.error(
                "Overage billing failed for client %s: %s",
                client.id,
                exc,
            )

    try:
        enforce_grace_period(db)
    except Exception as exc:
        logger.error("Grace period enforcement failed: %s", exc)


def main() -> None:
    """Scheduler entrypoint.

    Safe to run from cron or container.
    """
    db = SessionLocal()

    try:
        run_daily_jobs(db)
        db.commit()
        logger.info("Daily scheduler run completed successfully")
    except Exception as exc:
        db.rollback()
        logger.critical("Daily scheduler run failed: %s", exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
