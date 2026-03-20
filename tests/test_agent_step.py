"""Tests for AgentStep — retry, backoff, optional agents."""
import pytest
from unittest.mock import MagicMock, patch
from core.agent_step import AgentStep
from core.agents.base import AgentResult


def make_result(success=True, content="ok", error=""):
    return AgentResult(
        content=content if success else None,
        duration_ms=100,
        agent_name="test_agent",
        success=success,
        error=error,
    )


class TestAgentStep:
    def test_success_on_first_try(self):
        agent = MagicMock()
        agent.name = "test"
        agent.execute.return_value = make_result(success=True)

        step = AgentStep(agent, max_retries=3)
        result = step.execute({"keyword": "test"})

        assert result.success
        assert agent.execute.call_count == 1

    @patch("core.agent_step.time.sleep")
    def test_retry_then_success(self, mock_sleep):
        agent = MagicMock()
        agent.name = "test"
        agent.execute.side_effect = [
            make_result(success=False, error="API error 429"),
            make_result(success=False, error="API error 429"),
            make_result(success=True, content="recovered"),
        ]

        step = AgentStep(agent, max_retries=3, backoff_base=1)
        result = step.execute({"keyword": "test"})

        assert result.success
        assert result.content == "recovered"
        assert agent.execute.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("core.agent_step.time.sleep")
    def test_all_retries_exhausted(self, mock_sleep):
        agent = MagicMock()
        agent.name = "test"
        agent.execute.return_value = make_result(success=False, error="persistent error")

        step = AgentStep(agent, max_retries=2, backoff_base=1)
        result = step.execute({"keyword": "test"})

        assert not result.success
        assert agent.execute.call_count == 3  # 1 + 2 retries

    def test_no_retry_on_validation_error(self):
        agent = MagicMock()
        agent.name = "test"
        agent.execute.return_value = make_result(
            success=False, error="Validation failed: empty title"
        )

        step = AgentStep(agent, max_retries=3)
        result = step.execute({"keyword": "test"})

        assert not result.success
        assert agent.execute.call_count == 1  # No retries

    @patch("core.agent_step.time.sleep")
    def test_optional_agent_returns_failed_result(self, mock_sleep):
        agent = MagicMock()
        agent.name = "visual"
        agent.execute.return_value = make_result(success=False, error="Imagen API down")

        step = AgentStep(agent, max_retries=1, optional=True, backoff_base=1)
        result = step.execute({"keyword": "test"})

        assert not result.success  # Still reports failure
        # But no exception raised — pipeline can continue

    @patch("core.agent_step.time.sleep")
    def test_backoff_exponential(self, mock_sleep):
        agent = MagicMock()
        agent.name = "test"
        agent.execute.return_value = make_result(success=False, error="error")

        step = AgentStep(agent, max_retries=3, backoff_base=2, backoff_max=30)
        step.execute({"keyword": "test"})

        # Delays: 2*2^0=2, 2*2^1=4, 2*2^2=8
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [2, 4, 8]

    @patch("core.agent_step.time.sleep")
    def test_backoff_capped_at_max(self, mock_sleep):
        agent = MagicMock()
        agent.name = "test"
        agent.execute.return_value = make_result(success=False, error="error")

        step = AgentStep(agent, max_retries=5, backoff_base=2, backoff_max=10)
        step.execute({"keyword": "test"})

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert all(d <= 10 for d in delays)
