"""Admin authentication dependency."""

from fastapi import Header, HTTPException, status

from backend.app.core.config import settings


def require_admin(x_admin_key: str = Header(...)) -> None:
    """Ensure request is authenticated as admin.

    Admin access is granted via static API key header.
    """
    if not settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API key not configured",
        )

    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
