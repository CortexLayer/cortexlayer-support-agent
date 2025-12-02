"""Redis connection and utilities."""

import redis

from backend.app.core.config import settings
from backend.app.utils.logger import logger

try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
except Exception as e:
    logger.error(f"Redis init failed: {e}")
    redis_client = None


def test_redis_connection():
    """For Testing Redis Connection."""
    if redis_client is None:
        logger.error("❌ Redis not initialized")
        return False

    try:
        redis_client.ping()
        logger.info("✅ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False
