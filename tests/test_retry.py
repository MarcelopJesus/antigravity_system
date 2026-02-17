"""Tests for retry decorator (Story 1.3)."""
import pytest
from unittest.mock import patch
from core.retry import retry_with_backoff


class TestRetryWithBackoff:
    def test_succeeds_first_try(self):
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def always_works():
            return "ok"

        assert always_works() == "ok"

    def test_retries_on_recoverable_error(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def fails_then_works():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("500 Internal Server Error")
            return "recovered"

        result = fails_then_works()
        assert result == "recovered"
        assert call_count == 3

    def test_gives_up_after_max_retries(self):
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            raise Exception("500 Server Error")

        with pytest.raises(Exception, match="500"):
            always_fails()

    def test_no_retry_on_non_recoverable(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def auth_error():
            nonlocal call_count
            call_count += 1
            raise Exception("401 Unauthorized")

        with pytest.raises(Exception, match="401"):
            auth_error()

        assert call_count == 1

    def test_respects_total_timeout(self):
        call_count = 0

        @retry_with_backoff(max_retries=100, base_delay=0.01, total_timeout=0.05)
        def slow_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("500 timeout")

        with pytest.raises(Exception):
            slow_fail()

        # Should have stopped well before 100 retries
        assert call_count < 20
