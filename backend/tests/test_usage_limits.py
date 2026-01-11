"""Tests for plan limits and enforcement functions."""

import uuid
from datetime import datetime

import pytest
pytestmark = pytest.mark.integration

from backend.app.models.client import Client, PlanType
from backend.app.models.usage import UsageLog
from backend.app.services.usage_limits import (
    PLAN_LIMITS,
    check_document_limit,
    check_file_size,
    check_query_limit,
)


def test_check_query_limit_allows_within_limit(db) -> None:
    """Client under monthly query limit should pass without error."""
    client = Client(
        id=uuid.uuid4(),
        email="limit@test.com",
        hashed_password="x",
        company_name="TestCo",
        plan_type=PlanType.STARTER,
    )
    db.add(client)
    db.commit()

    # Insert fewer usage logs than plan limit
    limit = PLAN_LIMITS[PlanType.STARTER]["queries_per_month"]
    for _ in range(limit - 10):
        log = UsageLog(
            client_id=client.id,
            operation_type="query",
            timestamp=datetime.utcnow(),
        )
        db.add(log)
    db.commit()

    assert check_query_limit(client, db) is True


def test_check_query_limit_raises_when_exceeding_limit(db) -> None:
    """Exceeding monthly queries should raise HTTPException."""
    from fastapi import HTTPException

    client = Client(
        id=uuid.uuid4(),
        email="exceed@test.com",
        hashed_password="x",
        company_name="TestCo",
        plan_type=PlanType.STARTER,
    )
    db.add(client)
    db.commit()

    # Exceed limit
    limit = PLAN_LIMITS[PlanType.STARTER]["queries_per_month"]
    for _ in range(limit + 1):
        log = UsageLog(
            client_id=client.id,
            operation_type="query",
            timestamp=datetime.utcnow(),
        )
        db.add(log)
    db.commit()

    with pytest.raises(HTTPException):
        check_query_limit(client, db)


def test_check_document_limit(db) -> None:
    """Ensure doc upload limit works correctly."""
    from backend.app.models.documents import Document

    client = Client(
        id=uuid.uuid4(),
        email="docs@test.com",
        hashed_password="x",
        company_name="TestCo",
        plan_type=PlanType.STARTER,
    )
    db.add(client)
    db.commit()

    limit = PLAN_LIMITS[PlanType.STARTER]["max_docs"]

    # Add max docs
    for i in range(limit):
        doc = Document(
            client_id=client.id,
            filename=f"file_{i}.pdf",
            source_type="pdf",
            file_size_bytes=1000,
        )
        db.add(doc)
    db.commit()

    # Adding one more should raise
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        check_document_limit(client, db)


def test_check_file_size(db) -> None:
    """Ensure file size validation matches plan."""
    max_bytes = PLAN_LIMITS[PlanType.STARTER]["max_file_mb"] * 1024 * 1024

    assert check_file_size(max_bytes - 1, PlanType.STARTER)

    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        check_file_size(max_bytes + 1, PlanType.STARTER)
