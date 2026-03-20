"""LLMClient — Shared Gemini client with API key rotation, retry, rate limiting, and circuit breaker."""
import google.generativeai as genai
from config.settings import GOOGLE_API_KEYS_LIST, GEMINI_MODEL_NAME
from core.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Manages Gemini API access with key rotation, rate limiting, and circuit breaker."""

    def __init__(self, api_keys=None, model_name=None, rate_limiter=None, circuit_breaker=None):
        """
        Args:
            api_keys: List of API keys (default: from env).
            model_name: Gemini model name (default: from env).
            rate_limiter: Optional RateLimiter instance.
            circuit_breaker: Optional CircuitBreaker instance.
        """
        self.api_keys = api_keys or GOOGLE_API_KEYS_LIST
        if not self.api_keys:
            raise ValueError("GOOGLE_API_KEYS_LIST is not set or empty in environment.")

        self.model_name = model_name or GEMINI_MODEL_NAME
        self.current_key_index = 0
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker
        self._configure_current_key()

    def _configure_current_key(self):
        """Configures the Gemini library with the current key."""
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        logger.debug("Configured Gemini with API key #%d", self.current_key_index + 1)

    def _rotate_key(self):
        """Rotates to the next available API key."""
        if len(self.api_keys) <= 1:
            logger.error("Only one API key available, cannot rotate.")
            return False

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._configure_current_key()
        logger.info("Rotating to API Key #%d", self.current_key_index + 1)
        return True

    def execute_with_retry(self, func, *args, **kwargs):
        """Executes a function with retry logic, rate limiting, and circuit breaker."""
        # Check circuit breaker
        if self.circuit_breaker:
            self.circuit_breaker.allow_request()

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.throttle()

        max_retries = len(self.api_keys)
        attempts = 0

        while attempts < max_retries:
            try:
                result = func(*args, **kwargs)
                # Success — record it
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
                return result
            except Exception as e:
                error_str = str(e)
                if "400" in error_str or "429" in error_str or "403" in error_str or "API key expired" in error_str:
                    logger.warning("API Error with key #%d: %s", self.current_key_index + 1, e)
                    if self.circuit_breaker:
                        self.circuit_breaker.record_failure()
                    if not self._rotate_key():
                        raise e
                    attempts += 1
                else:
                    if self.circuit_breaker:
                        self.circuit_breaker.record_failure()
                    raise e

        raise Exception("All API keys failed.")

    def get_model(self):
        """Returns a configured GenerativeModel instance."""
        return genai.GenerativeModel(self.model_name)

    def generate(self, prompt, json_mode=False):
        """Generates content using the LLM with retry logic.

        Args:
            prompt: The prompt string to send.
            json_mode: If True, requests JSON response format.

        Returns:
            The raw response text.
        """
        def _task():
            model = self.get_model()
            config = {"response_mime_type": "application/json"} if json_mode else None
            response = model.generate_content(prompt, generation_config=config)
            return response.text

        return self.execute_with_retry(_task)
