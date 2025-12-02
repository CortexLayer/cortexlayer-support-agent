"""Rate limiting using Redis."""

from fastapi import HTTPException

from backend.app.utils.logger import logger
from backend.app.utils.redis_client import redis_client


async def check_rate_limit(client_id: str, limit_per_minute: int = 15) -> bool:
    """Enforce per-client rate limit.

    Raises HTTPException(429) if exceeded.
    """
    key = f"ratelimit:{client_id}"

    try:
        current = redis_client.get(key)

        if current is None:
            # first request in this 60-second window
            redis_client.setex(key, 60, 1)
            return True

        current = int(current)

        if current >= limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit_per_minute} requests per minute.",
            )

        redis_client.incr(key)
        return True

    except HTTPException:
        # bubble up rate-limit violations
        raise
    except Exception as exc:
        logger.error(f"Rate limit check failed: {exc}")
        # fail-open to avoid blocking business logic
        return True


def get_rate_limit_for_plan(plan_type: str) -> int:
    """Return rate limit based on subscription plan."""
    limits = {
        "starter": 15,
        "growth": 50,
        "scale": 100,
    }
    return limits.get(plan_type.lower(), 15)
