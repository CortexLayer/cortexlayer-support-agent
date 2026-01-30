"""Tests for admin authentication enforcement."""


def test_admin_route_rejects_missing_key(client):
    """Ensure admin routes reject requests without API key."""
    response = client.get("/admin/clients")
    assert response.status_code == 401


def test_admin_route_rejects_wrong_key(client):
    """Ensure admin routes reject requests with wrong API key."""
    response = client.get(
        "/admin/clients",
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_admin_route_accepts_valid_key(client, admin_headers):
    """Ensure admin routes accept valid admin API key."""
    response = client.get(
        "/admin/clients",
        headers=admin_headers,
    )
    assert response.status_code == 200
