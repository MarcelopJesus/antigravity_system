import time
import functools
from core.logger import get_logger

logger = get_logger(__name__)

# HTTP status codes that are recoverable (worth retrying)
RECOVERABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# HTTP status codes that should NOT be retried
NON_RECOVERABLE_STATUS_CODES = {400, 401, 403, 404}


def retry_with_backoff(max_retries=3, base_delay=2.0, max_delay=30.0, total_timeout=60.0):
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay between retries in seconds
        total_timeout: Maximum total time for all retries in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()

                    # Check if error is non-recoverable
                    is_non_recoverable = any(
                        str(code) in str(e) for code in NON_RECOVERABLE_STATUS_CODES
                    )
                    if is_non_recoverable and "429" not in str(e):
                        logger.error(
                            "%s failed with non-recoverable error (attempt %d/%d): %s",
                            func.__name__, attempt + 1, max_retries + 1, e
                        )
                        raise

                    # Check if we've exceeded total timeout
                    elapsed = time.time() - start_time
                    if elapsed >= total_timeout:
                        logger.error(
                            "%s exceeded total timeout (%.1fs). Giving up after %d attempts.",
                            func.__name__, total_timeout, attempt + 1
                        )
                        raise

                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)

                    # Ensure we won't exceed total timeout
                    remaining = total_timeout - elapsed
                    if delay > remaining:
                        delay = max(remaining - 1, 0)
                        if delay <= 0:
                            break

                    logger.warning(
                        "%s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        func.__name__, attempt + 1, max_retries + 1, e, delay
                    )
                    time.sleep(delay)

            # All retries exhausted
            logger.error(
                "%s failed after %d attempts. Last error: %s",
                func.__name__, max_retries + 1, last_exception
            )
            raise last_exception

        return wrapper
    return decorator
