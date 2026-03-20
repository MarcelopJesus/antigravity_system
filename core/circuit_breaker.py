"""CircuitBreaker — Prevents cascading failures by blocking calls to failing services."""
import time
import threading
from core.logger import get_logger

logger = get_logger(__name__)


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and requests are blocked."""
    pass


class CircuitBreaker:
    """Circuit breaker with CLOSED → OPEN → HALF_OPEN → CLOSED states.

    - CLOSED: Normal operation, requests pass through.
    - OPEN: Service is failing, requests are blocked.
    - HALF_OPEN: Testing if service recovered with one request.
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, name="default", failure_threshold=5, cooldown=60):
        """
        Args:
            name: Identifier for this circuit (e.g., "gemini", "wordpress").
            failure_threshold: Consecutive failures before opening (default: 5).
            cooldown: Seconds before trying half-open (default: 60).
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0
        self._lock = threading.Lock()

    @property
    def state(self):
        with self._lock:
            if self._state == self.OPEN:
                # Check if cooldown has passed
                if time.time() - self._last_failure_time >= self.cooldown:
                    self._state = self.HALF_OPEN
                    logger.info("Circuit '%s': OPEN → HALF_OPEN (cooldown expired)", self.name)
            return self._state

    def allow_request(self):
        """Check if a request should be allowed.

        Returns:
            True if request is allowed.

        Raises:
            CircuitOpenError if circuit is OPEN.
        """
        current = self.state
        if current == self.CLOSED:
            return True
        if current == self.HALF_OPEN:
            return True  # Allow one test request
        # OPEN
        raise CircuitOpenError(
            f"Circuit '{self.name}' is OPEN — service unavailable. "
            f"Retry after {self.cooldown}s cooldown."
        )

    def record_success(self):
        """Record a successful request. Resets failure count."""
        with self._lock:
            if self._state == self.HALF_OPEN:
                logger.info("Circuit '%s': HALF_OPEN → CLOSED (service recovered)", self.name)
            self._state = self.CLOSED
            self._failure_count = 0

    def record_failure(self):
        """Record a failed request. May open the circuit."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == self.HALF_OPEN:
                # Test request failed, back to OPEN
                self._state = self.OPEN
                logger.warning("Circuit '%s': HALF_OPEN → OPEN (test request failed)", self.name)

            elif self._failure_count >= self.failure_threshold:
                self._state = self.OPEN
                logger.warning(
                    "Circuit '%s': CLOSED → OPEN (%d consecutive failures)",
                    self.name, self._failure_count
                )

    def reset(self):
        """Manually reset the circuit to CLOSED."""
        with self._lock:
            self._state = self.CLOSED
            self._failure_count = 0
            logger.info("Circuit '%s': manually reset to CLOSED", self.name)

    @property
    def stats(self):
        with self._lock:
            return {
                "name": self.name,
                "state": self._state,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "cooldown": self.cooldown,
            }
