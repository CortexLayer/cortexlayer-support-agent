"""Pytest fixtures using the Docker PostgreSQL database.

Integration tests require the postgres container to be running.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.core.database import Base
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(scope="session")
def engine():
    """Create a single engine for the entire test session.

    Uses DATABASE_URL (Docker Postgres).
    """
    engine = create_engine(settings.DATABASE_URL)

    # Create all tables once
    Base.metadata.create_all(bind=engine)

    yield engine

    # Optional cleanup (safe to keep, safe to remove)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(engine):
    """Provide a transactional database session per test.

    Rolls back after each test.
    """
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client():
    return TestClient(app)