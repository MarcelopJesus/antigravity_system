"""Tests for Phase 6 — Advanced Optimization."""
import json
import pytest
from unittest.mock import patch, MagicMock

from core.seo.eeat import (
    generate_author_schema, generate_reviewed_by_html,
    enhance_article_schema_with_author, inject_author_badge,
)
from core.seo.featured_snippets import (
    detect_snippet_opportunities, format_paragraph_snippet,
    format_list_snippet, format_table_snippet,
)
from core.seo.ab_testing import create_ab_test, get_active_tests
from core.seo.entity_mapping import _parse_kg_response


# === Story 6.1 — E-E-A-T ===

class TestEEAT:

    def test_generate_author_schema(self):
        schema = generate_author_schema(
            "Marcelo Jesus",
            credentials="Hipnoterapeuta TRI",
            linkedin_url="https://linkedin.com/in/marcelo",
        )
        assert schema["name"] == "Marcelo Jesus"
        assert schema["jobTitle"] == "Hipnoterapeuta TRI"
        assert "https://linkedin.com/in/marcelo" in schema["sameAs"]

    def test_author_schema_minimal(self):
        schema = generate_author_schema("John")
        assert schema["name"] == "John"
        assert "sameAs" not in schema

    def test_reviewed_by_html(self):
        html = generate_reviewed_by_html("Marcelo Jesus", "Hipnoterapeuta TRI")
        assert "author-badge" in html
        assert "Marcelo Jesus" in html
        assert "Hipnoterapeuta TRI" in html

    def test_reviewed_by_empty(self):
        assert generate_reviewed_by_html("") == ""

    def test_enhance_article_schema(self):
        original = json.dumps({"@type": "Article", "headline": "Test"})
        enhanced = enhance_article_schema_with_author(original, {
            "name": "Marcelo",
            "credentials": "TRI",
            "linkedin_url": "https://linkedin.com/in/m",
        })
        data = json.loads(enhanced)
        assert data["author"]["name"] == "Marcelo"
        assert "sameAs" in data["author"]

    def test_inject_author_badge_before_cta(self):
        html = '<p>Content</p>\n<div class="cta-box"><p>CTA</p></div>'
        result = inject_author_badge(html, "Marcelo", "TRI")
        assert html.index("cta-box") > 0
        assert "author-badge" in result
        assert result.index("author-badge") < result.index("cta-box")


# === Story 6.2 — Featured Snippets ===

class TestFeaturedSnippets:

    def test_detect_opportunity_with_paa(self):
        brief = {
            "people_also_ask": [
                {"question": "O que é ansiedade?"},
                {"question": "Ansiedade tem cura?"},
            ]
        }
        result = detect_snippet_opportunities(brief)
        assert result is not None
        assert result["has_opportunity"] is True
        assert len(result["target_questions"]) == 2

    def test_no_opportunity_without_paa(self):
        result = detect_snippet_opportunities({"people_also_ask": []})
        assert result is None

    def test_format_paragraph_snippet(self):
        html = format_paragraph_snippet(
            "O que é ansiedade?",
            "A ansiedade é uma resposta natural do corpo ao estresse."
        )
        assert "<strong>O que é ansiedade?</strong>" in html

    def test_format_list_snippet(self):
        html = format_list_snippet(["Item 1", "Item 2", "Item 3"])
        assert "<ul>" in html
        assert "<li>Item 1</li>" in html

    def test_format_list_ordered(self):
        html = format_list_snippet(["Step 1", "Step 2"], ordered=True)
        assert "<ol>" in html

    def test_format_table_snippet(self):
        html = format_table_snippet(
            ["Tipo", "Duração"],
            [["Aguda", "Minutos"], ["Crônica", "Meses"]]
        )
        assert "<table>" in html
        assert "<th>Tipo</th>" in html
        assert "<td>Aguda</td>" in html


# === Story 6.3 — A/B Testing ===

class TestABTesting:

    def test_create_ab_test(self, tmp_path, monkeypatch):
        monkeypatch.setattr("core.seo.ab_testing.AB_TESTS_FILE", str(tmp_path / "tests.json"))
        test = create_ab_test(123, "ansiedade", {
            "titles": ["Título A", "Título B", "Título C"],
            "meta_descriptions": ["Meta A", "Meta B", "Meta C"],
        })
        assert test["post_id"] == 123
        assert test["status"] == "active"
        assert len(test["titles"]) == 3

    def test_get_active_tests(self, tmp_path, monkeypatch):
        monkeypatch.setattr("core.seo.ab_testing.AB_TESTS_FILE", str(tmp_path / "tests.json"))
        create_ab_test(1, "kw1", {"titles": ["A", "B"]})
        create_ab_test(2, "kw2", {"titles": ["C", "D"]})
        active = get_active_tests()
        assert len(active) == 2


# === Story 6.4 — Entity Mapping ===

class TestEntityMapping:

    def test_parse_kg_response(self):
        data = {
            "itemListElement": [
                {
                    "result": {
                        "name": "Ansiedade",
                        "@type": ["Thing", "MedicalCondition"],
                        "description": "Estado emocional",
                    },
                    "resultScore": 100,
                },
                {
                    "result": {
                        "name": "Terapia",
                        "@type": "Thing",
                        "description": "Tratamento",
                    },
                    "resultScore": 50,
                },
            ]
        }
        entities = _parse_kg_response(data)
        assert len(entities) == 2
        assert entities[0]["name"] == "Ansiedade"
        assert entities[0]["score"] == 100

    def test_parse_empty_response(self):
        assert _parse_kg_response({}) == []
        assert _parse_kg_response({"itemListElement": []}) == []
