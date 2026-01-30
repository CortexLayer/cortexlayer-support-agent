"""Tests conftest."""

import os

os.environ["ADMIN_API_KEY"] = "test-admin-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base, get_db
from backend.app.main import app

# DO NOT use :memory:
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture
def admin_headers():
    """Return valid admin authentication headers."""
    return {"X-Admin-Key": "test-admin-key"}


@pytest.fixture(scope="session")
def engine():
    """Create a single shared SQLite engine for all tests."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )

    # Clean slate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(engine):
    """Provide a transactional DB session per test."""
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


@pytest.fixture(autouse=True)
def override_get_db(db):
    """Force FastAPI to use the test DB session."""

    def _get_test_db():
        yield db

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client():
    """FastAPI test client."""
    return TestClient(app)
