"""Database engine and session maker for PostgreSQL."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings

# Create DB engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# SessionLocal = DB session per request
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db():
    """Provide a new database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
