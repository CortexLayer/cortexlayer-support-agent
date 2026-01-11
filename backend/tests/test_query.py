"""Test query endpoint authentication and validation."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_query_unauthorized():
    """Test that unauthenticated requests are rejected."""
    response = client.post("/query/", json={"query": "Test question"})
    assert response.status_code in (
        401,
        403,
    ), f"Expected 401/403, got {response.status_code}"


def test_query_empty_body():
    """Test that invalid auth token is checked even with empty body."""
    response = client.post(
        "/query/",
        headers={"Authorization": "Bearer invalidtoken"},
        json={},
    )

    assert (
        response.status_code == 401
    ), f"Expected 401 for invalid token, got {response.status_code}"


def test_query_invalid_token():
    """Test that invalid auth token is rejected."""
    response = client.post(
        "/query/",
        headers={"Authorization": "Bearer invalidtoken"},
        json={"query": "Test question"},
    )
    assert (
        response.status_code == 401
    ), f"Expected 401 for invalid token, got {response.status_code}"
