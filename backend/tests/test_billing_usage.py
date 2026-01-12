import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.core.database import Base
from backend.app.services.usage_logger import log_embedding_usage
from backend.app.models.usage_log import UsageLog


@pytest.fixture(scope="function")
def db():
    """
    Local DB fixture using dockerized PostgreSQL.
    Bypasses legacy pytest-postgresql conftest.
    """
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_log_embedding_usage(db):
    log_embedding_usage(
        db=db,
        client_id="test-client",
        tokens=100,
        cost_usd=0.002,
    )

    row = db.query(UsageLog).first()

    assert row is not None
    assert row.client_id == "test-client"
    assert row.embedding_tokens == 100
    assert row.cost_usd == 0.002
