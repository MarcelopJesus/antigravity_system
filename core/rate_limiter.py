"""RateLimiter — Sliding window rate limiter for API calls."""
import time
import threading
from collections import deque
from core.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Controls requests per minute using a sliding window algorithm.

    Thread-safe for use with multiple workers.
    """

    def __init__(self, rpm=15):
        """
        Args:
            rpm: Maximum requests per minute (default: 15 for Gemini free tier).
        """
        self.rpm = rpm
        self._timestamps = deque()
        self._lock = threading.Lock()
        self._total_waits = 0
        self._total_wait_time = 0.0

    def wait_if_needed(self):
        """Block if rate limit would be exceeded. Returns wait time in seconds.

        Returns:
            float: Time waited in seconds (0.0 if no wait needed).
        """
        with self._lock:
            now = time.time()

            # Remove timestamps older than 60 seconds
            while self._timestamps and now - self._timestamps[0] > 60:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.rpm:
                # Need to wait until oldest timestamp expires
                sleep_time = 60.0 - (now - self._timestamps[0]) + 0.1  # +0.1s buffer
                if sleep_time > 0:
                    self._total_waits += 1
                    self._total_wait_time += sleep_time
                    logger.info("Rate limit: waiting %.1fs (%d/%d RPM)", sleep_time, len(self._timestamps), self.rpm)
                    # Release lock during sleep so other threads aren't blocked unnecessarily
                    self._lock.release()
                    try:
                        time.sleep(sleep_time)
                    finally:
                        self._lock.acquire()
                    return sleep_time

            return 0.0

    def acquire(self):
        """Register a new request. Call after wait_if_needed()."""
        with self._lock:
            self._timestamps.append(time.time())

    def throttle(self):
        """Convenience: wait_if_needed() + acquire() in one call.

        Returns:
            float: Time waited in seconds.
        """
        waited = self.wait_if_needed()
        self.acquire()
        return waited

    @property
    def stats(self):
        """Return rate limiter statistics."""
        with self._lock:
            now = time.time()
            active = sum(1 for ts in self._timestamps if now - ts <= 60)
            return {
                "rpm_limit": self.rpm,
                "current_rpm": active,
                "total_waits": self._total_waits,
                "total_wait_time_s": round(self._total_wait_time, 1),
            }
