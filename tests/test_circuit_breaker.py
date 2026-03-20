"""Tests for CircuitBreaker — states, transitions, cooldown."""
import pytest
from unittest.mock import patch
from core.circuit_breaker import CircuitBreaker, CircuitOpenError


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker("test")
        assert cb.state == CircuitBreaker.CLOSED

    def test_allows_request_when_closed(self):
        cb = CircuitBreaker("test")
        assert cb.allow_request() is True

    def test_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreaker.CLOSED
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

    def test_blocks_request_when_open(self):
        cb = CircuitBreaker("test", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        with pytest.raises(CircuitOpenError):
            cb.allow_request()

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED
        assert cb.stats["failure_count"] == 0

    @patch("core.circuit_breaker.time.time")
    def test_half_open_after_cooldown(self, mock_time):
        cb = CircuitBreaker("test", failure_threshold=2, cooldown=60)

        # Open the circuit at t=100
        mock_time.return_value = 100
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

        # Still open at t=150
        mock_time.return_value = 150
        assert cb.state == CircuitBreaker.OPEN

        # Half-open at t=161
        mock_time.return_value = 161
        assert cb.state == CircuitBreaker.HALF_OPEN

    @patch("core.circuit_breaker.time.time")
    def test_half_open_success_closes(self, mock_time):
        cb = CircuitBreaker("test", failure_threshold=2, cooldown=10)

        mock_time.return_value = 100
        cb.record_failure()
        cb.record_failure()

        mock_time.return_value = 111  # Past cooldown
        assert cb.state == CircuitBreaker.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED

    @patch("core.circuit_breaker.time.time")
    def test_half_open_failure_reopens(self, mock_time):
        cb = CircuitBreaker("test", failure_threshold=2, cooldown=10)

        mock_time.return_value = 100
        cb.record_failure()
        cb.record_failure()

        mock_time.return_value = 111
        assert cb.state == CircuitBreaker.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

    def test_manual_reset(self):
        cb = CircuitBreaker("test", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreaker.OPEN

        cb.reset()
        assert cb.state == CircuitBreaker.CLOSED
        assert cb.stats["failure_count"] == 0

    def test_stats(self):
        cb = CircuitBreaker("gemini", failure_threshold=5, cooldown=30)
        cb.record_failure()
        stats = cb.stats
        assert stats["name"] == "gemini"
        assert stats["state"] == CircuitBreaker.CLOSED
        assert stats["failure_count"] == 1
