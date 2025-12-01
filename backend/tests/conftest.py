"""Pytest fixtures using a temporary PostgreSQL instance."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base


@pytest.fixture(scope="function")
def db(postgresql):
    """Use pytest-postgresql ephemeral PostgreSQL instance.

    Provides full PostgreSQL support: JSONB, UUID, etc.
    """
    host = postgresql.info.host
    port = postgresql.info.port
    user = postgresql.info.user
    password = postgresql.info.password
    dbname = postgresql.info.dbname

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

    engine = create_engine(url)

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
