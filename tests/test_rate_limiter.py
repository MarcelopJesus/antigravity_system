"""Tests for RateLimiter — sliding window, threading, throttle."""
import pytest
from unittest.mock import patch
from core.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_under_limit_no_wait(self):
        rl = RateLimiter(rpm=15)
        waited = rl.wait_if_needed()
        assert waited == 0.0

    @patch("core.rate_limiter.time.sleep")
    @patch("core.rate_limiter.time.time")
    def test_at_limit_waits(self, mock_time, mock_sleep):
        rl = RateLimiter(rpm=3)

        # Simulate 3 requests at t=0
        mock_time.return_value = 100.0
        for _ in range(3):
            rl.acquire()

        # 4th request should wait
        waited = rl.wait_if_needed()
        assert waited > 0
        assert mock_sleep.called

    def test_acquire_registers_timestamp(self):
        rl = RateLimiter(rpm=15)
        rl.acquire()
        assert rl.stats["current_rpm"] == 1

    def test_throttle_combines_wait_and_acquire(self):
        rl = RateLimiter(rpm=15)
        waited = rl.throttle()
        assert waited == 0.0
        assert rl.stats["current_rpm"] == 1

    def test_stats(self):
        rl = RateLimiter(rpm=10)
        rl.throttle()
        rl.throttle()

        stats = rl.stats
        assert stats["rpm_limit"] == 10
        assert stats["current_rpm"] == 2
        assert stats["total_waits"] == 0

    @patch("core.rate_limiter.time.time")
    def test_old_timestamps_cleaned(self, mock_time):
        rl = RateLimiter(rpm=2)

        # Add 2 requests at t=0
        mock_time.return_value = 100.0
        rl.acquire()
        rl.acquire()

        # At t=61, old timestamps should be cleaned
        mock_time.return_value = 161.0
        waited = rl.wait_if_needed()
        assert waited == 0.0  # Old entries expired, no wait needed
