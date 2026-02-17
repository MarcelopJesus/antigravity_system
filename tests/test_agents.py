"""Tests for modular agents (Story 2.2)."""
import json
import pytest
from unittest.mock import MagicMock, patch
from core.agents.base import BaseAgent, AgentResult
from core.agents.analyst import AnalystAgent
from core.agents.writer import WriterAgent
from core.agents.humanizer import HumanizerAgent
from core.agents.editor import EditorAgent
from core.agents.visual import VisualAgent
from core.agents.growth import GrowthAgent


def make_llm_client(response_text="mocked response"):
    """Creates a mock LLMClient that returns the given text."""
    llm = MagicMock()
    llm.generate.return_value = response_text
    llm.api_keys = ["key1", "key2"]
    llm.current_key_index = 0
    return llm


def make_kb(load_return="", voice_return=""):
    """Creates a mock KnowledgeBase."""
    kb = MagicMock()
    kb.load.return_value = load_return
    kb.load_voice_guide.return_value = voice_return
    return kb


# ──────────────────────────────────────────────
# AgentResult
# ──────────────────────────────────────────────

class TestAgentResult:
    def test_dataclass_fields(self):
        r = AgentResult(content="ok", duration_ms=100, agent_name="test", success=True)
        assert r.content == "ok"
        assert r.duration_ms == 100
        assert r.agent_name == "test"
        assert r.success is True
        assert r.error == ""

    def test_failed_result(self):
        r = AgentResult(content=None, duration_ms=50, agent_name="test", success=False, error="boom")
        assert r.success is False
        assert r.error == "boom"


# ──────────────────────────────────────────────
# BaseAgent.clean_llm_output
# ──────────────────────────────────────────────

class TestCleanLlmOutput:
    def test_removes_html_code_block(self):
        text = "```html\n<h1>Title</h1>\n```"
        assert "<h1>Title</h1>" == BaseAgent.clean_llm_output(text)

    def test_removes_plain_code_block(self):
        text = "```\n<p>Content</p>\n```"
        assert "<p>Content</p>" == BaseAgent.clean_llm_output(text)

    def test_clean_text_unchanged(self):
        text = "<h1>Title</h1><p>Content</p>"
        assert text == BaseAgent.clean_llm_output(text)


# ──────────────────────────────────────────────
# AnalystAgent
# ──────────────────────────────────────────────

class TestAnalystAgent:
    def test_execute_parses_json(self):
        response = json.dumps({"title": "Test", "sections": [{"h2": "Intro"}]})
        llm = make_llm_client(response)
        kb = make_kb(load_return="kb content")

        agent = AnalystAgent(llm, kb)
        result = agent.execute({"keyword": "ansiedade", "links_inventory": []})

        assert result.success is True
        assert result.content["title"] == "Test"
        assert result.agent_name == "analyst"
        assert result.duration_ms > 0

    def test_execute_handles_markdown_wrapped_json(self):
        response = '```json\n{"title": "Test", "sections": []}\n```'
        llm = make_llm_client(response)
        agent = AnalystAgent(llm, make_kb())
        result = agent.execute({"keyword": "tri", "links_inventory": []})

        assert result.success is True
        assert result.content["title"] == "Test"

    def test_execute_with_dict_links(self):
        response = json.dumps({"title": "T", "sections": []})
        llm = make_llm_client(response)
        agent = AnalystAgent(llm, make_kb())
        result = agent.execute({
            "keyword": "test",
            "links_inventory": [{"keyword": "link1", "url": "http://example.com"}]
        })
        assert result.success is True

    def test_execute_failure_returns_error(self):
        llm = make_llm_client()
        llm.generate.side_effect = Exception("API error")
        agent = AnalystAgent(llm, make_kb())
        result = agent.execute({"keyword": "test", "links_inventory": []})

        assert result.success is False
        assert "API error" in result.error


# ──────────────────────────────────────────────
# WriterAgent
# ──────────────────────────────────────────────

class TestWriterAgent:
    def test_execute_returns_raw_text(self):
        llm = make_llm_client("<h1>Article</h1><p>Content here</p>")
        agent = WriterAgent(llm, make_kb())
        result = agent.execute({"title": "Test", "sections": []})

        assert result.success is True
        assert "<h1>Article</h1>" in result.content


# ──────────────────────────────────────────────
# HumanizerAgent
# ──────────────────────────────────────────────

class TestHumanizerAgent:
    def test_execute_cleans_code_blocks(self):
        llm = make_llm_client("```html\n<h1>Humanized</h1>\n```")
        kb = make_kb(voice_return="voice guide text")
        agent = HumanizerAgent(llm, kb)
        result = agent.execute("<h1>Draft</h1>")

        assert result.success is True
        assert "```" not in result.content
        assert "<h1>Humanized</h1>" == result.content

    def test_loads_voice_guide(self):
        llm = make_llm_client("<p>content</p>")
        kb = make_kb(voice_return="my voice guide")
        agent = HumanizerAgent(llm, kb)
        agent.execute("<p>draft</p>")

        kb.load_voice_guide.assert_called_once()


# ──────────────────────────────────────────────
# EditorAgent
# ──────────────────────────────────────────────

class TestEditorAgent:
    def test_execute_cleans_code_blocks(self):
        llm = make_llm_client("```html\n<h1>Title</h1><p>Content</p>\n```")
        agent = EditorAgent(llm, make_kb())
        result = agent.execute("<p>draft</p>")

        assert result.success is True
        assert not result.content.startswith("```")
        assert "<h1>" in result.content

    def test_converts_markdown_to_html(self):
        llm = make_llm_client("## Title\n\n**Bold text** and more content")
        agent = EditorAgent(llm, make_kb())
        result = agent.execute("<p>draft</p>")

        assert result.success is True
        assert "##" not in result.content
        assert "**" not in result.content

    def test_strips_conversational_prefix(self):
        llm = make_llm_client("Here is the article:\n<h1>Title</h1><p>Content</p>")
        agent = EditorAgent(llm, make_kb())
        result = agent.execute("<p>draft</p>")

        assert result.success is True
        assert result.content.startswith("<h1>")


# ──────────────────────────────────────────────
# GrowthAgent
# ──────────────────────────────────────────────

class TestGrowthAgent:
    def test_execute_returns_suggestions(self):
        llm = make_llm_client("- Topic One\n- Topic Two\n- Topic Three")
        agent = GrowthAgent(llm, make_kb())
        result = agent.execute({"title": "Test Article"})

        assert result.success is True
        assert len(result.content) == 2
        assert "Topic One" in result.content[0]

    def test_limits_to_two_suggestions(self):
        llm = make_llm_client("A\nB\nC\nD\nE")
        agent = GrowthAgent(llm, make_kb())
        result = agent.execute({"title": "Test"})

        assert len(result.content) == 2


# ──────────────────────────────────────────────
# VisualAgent (prompt generation only — no network)
# ──────────────────────────────────────────────

class TestVisualAgent:
    def test_execute_returns_prompts(self):
        llm = make_llm_client("prompt one description ||| prompt two description")
        agent = VisualAgent(llm, make_kb())
        result = agent.execute("<h1>Article</h1><p>Content</p>")

        assert result.success is True
        assert "|||" in result.content

    def test_is_valid_image_jpeg(self, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
        assert VisualAgent._is_valid_image(img) is True

    def test_is_valid_image_png(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b'\x89PNG' + b'\x00' * 100)
        assert VisualAgent._is_valid_image(img) is True

    def test_is_valid_image_invalid(self, tmp_path):
        img = tmp_path / "test.heic"
        img.write_bytes(b'\x00\x00\x00\x18ftypheic')
        assert VisualAgent._is_valid_image(img) is False
