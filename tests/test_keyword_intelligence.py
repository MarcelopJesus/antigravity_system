"""Tests for Story 7.2 — Keyword Intelligence."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.prompts import CONTENT_ANALYST_PROMPT, SENIOR_WRITER_PROMPT
from core.pipeline import PipelineResult
from core.dry_run import save_dry_run_output


class TestAnalystPromptKeywordFields:
    """Verify the Analyst prompt requests semantic keyword fields."""

    def test_prompt_requests_search_intent(self):
        assert "search_intent" in CONTENT_ANALYST_PROMPT

    def test_prompt_requests_keyword_variations(self):
        assert "keyword_variations" in CONTENT_ANALYST_PROMPT

    def test_prompt_requests_lsi_keywords(self):
        assert "lsi_keywords" in CONTENT_ANALYST_PROMPT

    def test_prompt_has_intent_options(self):
        assert "informational" in CONTENT_ANALYST_PROMPT
        assert "transactional" in CONTENT_ANALYST_PROMPT
        assert "navigational" in CONTENT_ANALYST_PROMPT


class TestWriterPromptKeywordFields:
    """Verify the Writer prompt accepts semantic keyword placeholders."""

    def test_prompt_has_keyword_variations_placeholder(self):
        assert "{keyword_variations}" in SENIOR_WRITER_PROMPT

    def test_prompt_has_lsi_keywords_placeholder(self):
        assert "{lsi_keywords}" in SENIOR_WRITER_PROMPT

    def test_prompt_format_with_values(self):
        formatted = SENIOR_WRITER_PROMPT.format(
            outline_json="{}",
            keyword_variations="ansiedade social, ansiedade crônica, crise de ansiedade",
            lsi_keywords="terapia, saúde mental, bem-estar, estresse, pânico",
            knowledge_base="KB content here",
            local_seo_section="",
        )
        assert "ansiedade social" in formatted
        assert "saúde mental" in formatted

    def test_prompt_format_with_na_fallback(self):
        formatted = SENIOR_WRITER_PROMPT.format(
            outline_json="{}",
            keyword_variations="N/A",
            lsi_keywords="N/A",
            knowledge_base="KB",
            local_seo_section="",
        )
        assert "N/A" in formatted


class TestWriterAgentKeywordExtraction:
    """Test that WriterAgent correctly extracts keyword fields from outline."""

    def test_writer_formats_keywords(self):
        from unittest.mock import MagicMock
        from core.agents.writer import WriterAgent

        mock_llm = MagicMock()
        agent = WriterAgent(mock_llm, knowledge_base=None)

        outline = {
            "title": "Test",
            "keyword_variations": ["var1", "var2", "var3"],
            "lsi_keywords": ["lsi1", "lsi2"],
            "outline": [],
        }
        prompt = agent._build_prompt(outline)
        assert "var1, var2, var3" in prompt
        assert "lsi1, lsi2" in prompt

    def test_writer_handles_missing_keywords(self):
        from unittest.mock import MagicMock
        from core.agents.writer import WriterAgent

        mock_llm = MagicMock()
        agent = WriterAgent(mock_llm, knowledge_base=None)

        outline = {"title": "Test", "outline": []}
        prompt = agent._build_prompt(outline)
        assert "N/A" in prompt


class TestPipelineResultKeywordFields:
    """Test PipelineResult has the new keyword intelligence fields."""

    def test_default_values(self):
        r = PipelineResult(success=True)
        assert r.search_intent == ""
        assert r.keyword_variations == []
        assert r.lsi_keywords == []

    def test_set_values(self):
        r = PipelineResult(
            success=True,
            search_intent="informational",
            keyword_variations=["v1", "v2"],
            lsi_keywords=["l1", "l2", "l3"],
        )
        assert r.search_intent == "informational"
        assert len(r.keyword_variations) == 2
        assert len(r.lsi_keywords) == 3


class TestDryRunKeywordMetrics:
    """Test that dry-run output includes keyword intelligence metrics."""

    def test_metrics_json_includes_keyword_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = PipelineResult(
            success=True,
            title="Test Article",
            content="<h1>Test</h1><p>Content</p>",
            meta_description="Meta test",
            search_intent="informational",
            keyword_variations=["var1", "var2"],
            lsi_keywords=["lsi1", "lsi2", "lsi3"],
        )
        _, json_path = save_dry_run_output("co1", "test keyword", result)

        with open(json_path, 'r') as f:
            metrics = json.load(f)

        assert metrics['search_intent'] == "informational"
        assert metrics['keyword_variations'] == ["var1", "var2"]
        assert metrics['lsi_keywords'] == ["lsi1", "lsi2", "lsi3"]
