"""Tests for ArticlePipeline (Story 2.3)."""
import json
import pytest
from unittest.mock import MagicMock, patch
from core.pipeline import (
    ArticlePipeline,
    PipelineResult,
    validate_keyword,
    validate_analyst_output,
    validate_html_output,
    clean_orphan_placeholders,
)
from core.llm_client import LLMClient
from core.knowledge_base import KnowledgeBase


def make_mock_llm():
    """Creates a mock LLMClient."""
    llm = MagicMock(spec=LLMClient)
    llm.api_keys = ["key1", "key2"]
    llm.current_key_index = 0
    return llm


def make_mock_kb():
    """Creates a mock KnowledgeBase."""
    kb = MagicMock(spec=KnowledgeBase)
    kb.load.return_value = ""
    kb.load_voice_guide.return_value = ""
    return kb


# ──────────────────────────────────────────────
# Validation functions (re-exported from pipeline)
# ──────────────────────────────────────────────

class TestValidateKeyword:
    def test_valid(self):
        ok, err = validate_keyword("terapia tri", set())
        assert ok is True

    def test_empty(self):
        ok, err = validate_keyword("", set())
        assert ok is False

    def test_duplicate(self):
        ok, err = validate_keyword("test", {"test"})
        assert ok is False


class TestValidateAnalystOutput:
    def test_valid(self):
        ok, _ = validate_analyst_output({"title": "T", "sections": []})
        assert ok is True

    def test_missing_title(self):
        ok, _ = validate_analyst_output({"sections": []})
        assert ok is False

    def test_not_dict(self):
        ok, _ = validate_analyst_output("string")
        assert ok is False


class TestValidateHtmlOutput:
    def test_valid(self):
        html = "<h1>Title</h1>" + "<p>Content paragraph.</p>" * 10
        ok, _ = validate_html_output(html, "Writer")
        assert ok is True

    def test_empty(self):
        ok, _ = validate_html_output("", "Writer")
        assert ok is False

    def test_too_short(self):
        ok, _ = validate_html_output("<p>Hi</p>", "Writer")
        assert ok is False


class TestCleanOrphanPlaceholders:
    def test_removes(self):
        assert "AB" == clean_orphan_placeholders("A<!-- IMG_PLACEHOLDER -->B")

    def test_noop(self):
        assert "<p>ok</p>" == clean_orphan_placeholders("<p>ok</p>")


# ──────────────────────────────────────────────
# PipelineResult
# ──────────────────────────────────────────────

class TestPipelineResult:
    def test_success_result(self):
        r = PipelineResult(success=True, title="Test", content="<p>ok</p>")
        assert r.success is True
        assert r.title == "Test"
        assert r.error == ""

    def test_failure_result(self):
        r = PipelineResult(success=False, error="boom")
        assert r.success is False
        assert r.error == "boom"


# ──────────────────────────────────────────────
# ArticlePipeline end-to-end (with mocks)
# ──────────────────────────────────────────────

class TestArticlePipelineE2E:
    def _setup_pipeline_with_responses(self, analyst_response, writer_response, humanizer_response, editor_response):
        """Helper to build pipeline with specific LLM responses per agent call."""
        llm = make_mock_llm()
        kb = make_mock_kb()

        # generate() is called sequentially by each agent
        llm.generate.side_effect = [
            analyst_response,
            writer_response,
            humanizer_response,
            editor_response,
        ]

        pipeline = ArticlePipeline(llm, kb)
        return pipeline

    def test_full_pipeline_success(self):
        analyst_json = json.dumps({
            "title": "Artigo sobre Ansiedade",
            "sections": [{"h2": "Intro"}],
            "meta_description": "Meta desc"
        })
        writer_html = "<h1>Artigo sobre Ansiedade</h1><p>" + "Conteudo do artigo. " * 20 + "</p>"
        humanizer_html = "<h1>Artigo sobre Ansiedade</h1><p>" + "Conteudo humanizado. " * 20 + "</p>"
        editor_html = "<h1>Artigo sobre Ansiedade</h1><p>" + "Conteudo final editado. " * 20 + "</p>"

        pipeline = self._setup_pipeline_with_responses(
            analyst_json, writer_html, humanizer_html, editor_html
        )
        result = pipeline.run("ansiedade", [])

        assert result.success is True
        assert result.title == "Artigo sobre Ansiedade"
        assert "<h1>" in result.content
        assert len(result.agent_metrics) == 4
        assert result.total_duration_ms > 0

    def test_analyst_failure_stops_pipeline(self):
        llm = make_mock_llm()
        llm.generate.side_effect = Exception("API Error")
        kb = make_mock_kb()
        pipeline = ArticlePipeline(llm, kb)

        result = pipeline.run("test", [])

        assert result.success is False
        assert "Analyst failed" in result.error
        assert len(result.agent_metrics) == 1

    def test_analyst_invalid_json_stops_pipeline(self):
        llm = make_mock_llm()
        llm.generate.return_value = "not valid json at all"
        kb = make_mock_kb()
        pipeline = ArticlePipeline(llm, kb)

        result = pipeline.run("test", [])

        assert result.success is False
        assert "Analyst failed" in result.error

    def test_analyst_missing_title_stops_pipeline(self):
        llm = make_mock_llm()
        llm.generate.return_value = json.dumps({"sections": []})
        kb = make_mock_kb()
        pipeline = ArticlePipeline(llm, kb)

        result = pipeline.run("test", [])

        assert result.success is False
        assert "validation failed" in result.error

    def test_writer_empty_output_stops_pipeline(self):
        analyst_json = json.dumps({"title": "T", "sections": [{"h2": "S"}]})

        pipeline = self._setup_pipeline_with_responses(
            analyst_json, "", "humanized", "edited"
        )
        result = pipeline.run("test", [])

        assert result.success is False
        assert "Writer validation failed" in result.error
        assert len(result.agent_metrics) == 2

    def test_metrics_collected(self):
        analyst_json = json.dumps({"title": "T", "sections": [], "meta_description": ""})
        long_content = "<h1>T</h1><p>" + "word " * 50 + "</p>"

        pipeline = self._setup_pipeline_with_responses(
            analyst_json, long_content, long_content, long_content
        )
        result = pipeline.run("test", [])

        assert result.success is True
        for metric in result.agent_metrics:
            assert metric.duration_ms >= 0
            assert metric.agent_name != ""


# ──────────────────────────────────────────────
# GeminiBrain facade backward compat
# ──────────────────────────────────────────────

class TestGeminiBrainFacade:
    def test_facade_analyze_and_plan(self):
        with patch("core.gemini_brain.LLMClient") as MockLLM:
            mock_llm = MagicMock()
            mock_llm.api_keys = ["k1", "k2"]
            mock_llm.current_key_index = 0
            mock_llm.generate.return_value = json.dumps({"title": "T", "sections": []})
            MockLLM.return_value = mock_llm

            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb")
            result = brain.analyze_and_plan("test", [])

            assert result["title"] == "T"

    def test_facade_has_expected_methods(self):
        with patch("core.gemini_brain.LLMClient") as MockLLM:
            mock_llm = MagicMock()
            mock_llm.api_keys = ["k1"]
            mock_llm.current_key_index = 0
            MockLLM.return_value = mock_llm

            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp")

            assert hasattr(brain, 'analyze_and_plan')
            assert hasattr(brain, 'write_article_body')
            assert hasattr(brain, 'humanize_with_tri_voice')
            assert hasattr(brain, 'edit_and_refine')
            assert hasattr(brain, 'generate_image_prompts')
            assert hasattr(brain, 'generate_final_images')
            assert hasattr(brain, 'get_real_author_photo')
            assert hasattr(brain, 'identify_new_topics')
            assert hasattr(brain, '_load_knowledge_base')
            assert hasattr(brain, '_load_voice_guide')
            assert hasattr(brain, '_rotate_key')
