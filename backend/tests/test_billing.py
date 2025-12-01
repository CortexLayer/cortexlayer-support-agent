"""Tests for billing calculation utils and usage logging."""

import uuid

from backend.app.models.client import Client
from backend.app.models.usage import UsageLog
from backend.app.services import billing as billing_svc


def test_embedding_cost_basic() -> None:
    """Ensure embedding cost calculation returns correct non-zero value."""
    cost = billing_svc.calculate_embedding_cost(1_000_000)
    assert cost > 0
    assert cost < 1


def test_generation_cost_nonzero() -> None:
    """Ensure generation cost calculation computes correct cost based on tokens."""
    cost = billing_svc.calculate_generation_cost(
        input_tokens=10_000,
        output_tokens=5_000,
        model="mixtral-8x7b",
    )
    assert cost > 0


def test_log_usage_inserts_row(db) -> None:
    """Ensure log_usage() inserts a UsageLog row with correct fields."""
    client = Client(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="x",
        company_name="TestCo",
    )
    db.add(client)
    db.commit()

    billing_svc.log_usage(
        db=db,
        client_id=client.id,
        operation_type="query",
        input_tokens=100,
        output_tokens=50,
        model_used="mixtral-8x7b",
    )
    db.commit()

    rows = db.query(UsageLog).filter(UsageLog.client_id == client.id).all()
    assert len(rows) == 1
    assert rows[0].input_tokens == 100
    assert rows[0].output_tokens == 50
    assert rows[0].operation_type == "query"
