"""Tests for GeminiBrain facade (Story 1.7, updated for Story 2.4)."""
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestGeminiBrainInit:
    def test_init_with_valid_keys(self):
        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1", "key2"]):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb")
            assert len(brain.api_keys) == 2
            assert brain.current_key_index == 0

    def test_init_without_keys_raises(self):
        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", []):
            # Need to reload to pick up new value
            from core.llm_client import LLMClient
            with pytest.raises(ValueError, match="not set or empty"):
                LLMClient(api_keys=[])


class TestKeyRotation:
    def test_rotate_key_cycles(self):
        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1", "key2"]):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb")
            initial_index = brain.llm.current_key_index
            result = brain._rotate_key()
            assert result is True
            assert brain.llm.current_key_index != initial_index

    def test_rotate_key_single_key_fails(self):
        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["only_one_key"]):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb")
            result = brain._rotate_key()
            assert result is False


class TestKnowledgeBase:
    def test_load_kb_nonexistent_path(self):
        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1"]):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb_path_12345")
            result = brain._load_knowledge_base()
            assert result == ""

    def test_load_kb_with_files(self, tmp_path):
        # Create fake KB files
        (tmp_path / "TRI_ESSENCIA.txt").write_text("essencia content", encoding="utf-8")
        (tmp_path / "TRI_VOZ.txt").write_text("voz content", encoding="utf-8")
        (tmp_path / "other_file.txt").write_text("other content", encoding="utf-8")

        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1"]):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path=str(tmp_path))

            result = brain._load_knowledge_base(file_filter=["tri_essencia"])
            assert "essencia content" in result
            assert "voz content" not in result
            assert "other content" not in result

    def test_load_voice_guide(self, tmp_path):
        (tmp_path / "TRI_VOZ.txt").write_text("voice guide content", encoding="utf-8")

        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1"]):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path=str(tmp_path))

            result = brain._load_voice_guide()
            assert "voice guide content" in result

    def test_load_voice_guide_missing(self, tmp_path):
        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1"]):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path=str(tmp_path))

            result = brain._load_voice_guide()
            assert result == ""


class TestAnalyzeAndPlan:
    def test_parse_valid_json_response(self):
        response_text = json.dumps({
            "title": "Test Article",
            "sections": [{"h2": "Intro"}],
            "meta_description": "Test desc"
        })

        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1"]), \
             patch("core.llm_client.LLMClient.generate", return_value=response_text):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb")
            result = brain.analyze_and_plan("test keyword", [])

        assert result["title"] == "Test Article"
        assert "sections" in result

    def test_parse_json_with_markdown_wrapper(self):
        raw = '```json\n{"title": "Test", "sections": []}\n```'

        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1"]), \
             patch("core.llm_client.LLMClient.generate", return_value=raw):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb")
            result = brain.analyze_and_plan("keyword", [])

        assert result["title"] == "Test"


class TestHtmlCleanup:
    def test_edit_and_refine_cleans_markdown(self):
        response_text = "## Title\n\n**Bold text** and more content"

        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1"]), \
             patch("core.llm_client.LLMClient.generate", return_value=response_text):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb")
            result = brain.edit_and_refine("<p>draft</p>")

        # Should be converted to HTML
        assert "##" not in result
        assert "**" not in result
        assert "<h2>" in result or "<strong>" in result

    def test_edit_and_refine_strips_code_blocks(self):
        response_text = "```html\n<h1>Title</h1><p>Content</p>\n```"

        with patch("core.llm_client.GOOGLE_API_KEYS_LIST", ["key1"]), \
             patch("core.llm_client.LLMClient.generate", return_value=response_text):
            from core.gemini_brain import GeminiBrain
            brain = GeminiBrain(knowledge_base_path="/tmp/nonexistent_kb")
            result = brain.edit_and_refine("<p>draft</p>")

        assert not result.startswith("```")
        assert "<h1>" in result
