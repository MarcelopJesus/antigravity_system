"""Queue configuration — Redis connection and availability check."""
import os
from core.logger import get_logger

logger = get_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_redis_connection():
    """Get a Redis connection. Returns None if Redis is unavailable."""
    try:
        from redis import Redis
        conn = Redis.from_url(REDIS_URL)
        conn.ping()
        logger.debug("Redis connected: %s", REDIS_URL)
        return conn
    except Exception as e:
        logger.debug("Redis unavailable: %s", e)
        return None


def is_redis_available():
    """Check if Redis is available."""
    conn = get_redis_connection()
    if conn:
        conn.close()
        return True
    return False
