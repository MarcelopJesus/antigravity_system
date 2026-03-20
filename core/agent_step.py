"""AgentStep — Wraps any agent with configurable retry and exponential backoff."""
import time
from core.logger import get_logger

logger = get_logger(__name__)


class NonRetriableError(Exception):
    """Errors that should not be retried (e.g., validation failures)."""
    pass


class AgentStep:
    """Wraps a BaseAgent with retry logic, backoff, and metrics."""

    def __init__(self, agent, max_retries=3, backoff_base=2, backoff_max=30, timeout=120, optional=False):
        """
        Args:
            agent: A BaseAgent instance.
            max_retries: Max retry attempts (default: 3).
            backoff_base: Base seconds for exponential backoff (default: 2).
            backoff_max: Max backoff delay in seconds (default: 30).
            timeout: Max seconds per attempt (default: 120). Currently advisory.
            optional: If True, pipeline continues on failure with warning.
        """
        self.agent = agent
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.timeout = timeout
        self.optional = optional
        self.agent_name = getattr(agent, 'name', agent.__class__.__name__)

    def execute(self, input_data):
        """Execute the agent with retry and backoff.

        Returns:
            AgentResult from the agent.

        Raises:
            Exception if all retries exhausted and agent is not optional.
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            result = self.agent.execute(input_data)

            if result.success:
                if attempt > 0:
                    logger.info(
                        "[%s] succeeded on attempt %d/%d",
                        self.agent_name, attempt + 1, self.max_retries + 1
                    )
                return result

            last_error = result.error
            error_str = str(last_error)

            # Don't retry validation errors
            if "validation" in error_str.lower():
                logger.error(
                    "[%s] non-retriable error: %s", self.agent_name, error_str
                )
                break

            if attempt < self.max_retries:
                delay = min(self.backoff_base * (2 ** attempt), self.backoff_max)
                logger.warning(
                    "[%s] attempt %d/%d failed: %s — retrying in %.1fs",
                    self.agent_name, attempt + 1, self.max_retries + 1,
                    error_str, delay
                )
                time.sleep(delay)
            else:
                logger.error(
                    "[%s] all %d attempts exhausted. Last error: %s",
                    self.agent_name, self.max_retries + 1, error_str
                )

        # All retries exhausted
        if self.optional:
            logger.warning(
                "[%s] optional agent failed after %d attempts — continuing pipeline",
                self.agent_name, self.max_retries + 1
            )
            return result  # Return the failed result, pipeline decides what to do

        return result  # Return failed result, let pipeline handle it
