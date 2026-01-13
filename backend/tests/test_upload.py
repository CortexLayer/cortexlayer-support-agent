"""Test upload endpoints."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_upload_requires_auth():
    """Test that upload requires authentication."""
    response = client.post("/upload/file")
    assert response.status_code in (401, 403)
