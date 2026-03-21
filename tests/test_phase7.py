"""Tests for Phase 7 — Scale."""
import json
import pytest
from unittest.mock import patch, MagicMock

from core.keyword_discovery.discovery import (
    expand_with_modifiers, google_suggest, discover_keywords,
)
from core.seo.multilang import (
    generate_hreflang_tags, generate_hreflang_schema,
    get_language_config, LANGUAGE_CONFIGS,
)
from core.dashboard.multi_tenant import MultiTenantDashboard


# === Story 7.1 — Keyword Discovery ===

class TestExpandModifiers:

    def test_generates_prefix_and_suffix(self):
        expanded = expand_with_modifiers("ansiedade")
        assert any("como" in kw for kw in expanded)
        assert any("tratamento" in kw for kw in expanded)
        assert len(expanded) > 10

    def test_includes_keyword(self):
        expanded = expand_with_modifiers("terapia")
        assert all("terapia" in kw for kw in expanded)


class TestGoogleSuggest:

    @patch("core.keyword_discovery.discovery.requests.get")
    def test_returns_suggestions(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["ansiedade", ["ansiedade generalizada", "ansiedade sintomas", "ansiedade tratamento"]]
        mock_get.return_value = mock_response

        results = google_suggest("ansiedade")
        assert len(results) == 3
        assert "ansiedade generalizada" in results

    @patch("core.keyword_discovery.discovery.requests.get")
    def test_filters_original_query(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["ansiedade", ["ansiedade", "ansiedade tratamento"]]
        mock_get.return_value = mock_response

        results = google_suggest("ansiedade")
        assert "ansiedade" not in [r.lower() for r in results]

    @patch("core.keyword_discovery.discovery.requests.get")
    def test_handles_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        results = google_suggest("test")
        assert results == []


class TestDiscoverKeywords:

    @patch("core.keyword_discovery.discovery.google_suggest")
    @patch("core.keyword_discovery.discovery.generate_serp_brief")
    def test_discovers_from_multiple_sources(self, mock_serp, mock_suggest):
        mock_suggest.return_value = ["ansiedade generalizada", "ansiedade sintomas"]
        mock_serp.return_value = {
            "related_searches": ["como tratar ansiedade"],
            "people_also_ask": [{"question": "Ansiedade tem cura?"}],
        }

        results = discover_keywords("ansiedade", existing_keywords=set())
        keywords = [r["keyword"] for r in results]
        assert "ansiedade generalizada" in keywords or "como tratar ansiedade" in keywords
        assert len(results) > 0

    @patch("core.keyword_discovery.discovery.google_suggest")
    @patch("core.keyword_discovery.discovery.generate_serp_brief")
    def test_filters_existing(self, mock_serp, mock_suggest):
        mock_suggest.return_value = ["ansiedade generalizada", "ansiedade nova"]
        mock_serp.return_value = {}

        results = discover_keywords("ansiedade", existing_keywords={"ansiedade generalizada"})
        keywords = [r["keyword"].lower() for r in results]
        assert "ansiedade generalizada" not in keywords


# === Story 7.3 — Multi-Language ===

class TestMultiLang:

    def test_hreflang_tags(self):
        translations = {
            "pt-br": "https://site.com/ansiedade",
            "en": "https://site.com/en/anxiety",
        }
        tags = generate_hreflang_tags("https://site.com/ansiedade", translations)
        assert 'hreflang="pt-br"' in tags
        assert 'hreflang="en"' in tags
        assert 'hreflang="x-default"' in tags

    def test_hreflang_too_few_langs(self):
        translations = {"pt-br": "https://site.com/test"}
        assert generate_hreflang_tags("https://site.com/test", translations) == ""

    def test_hreflang_schema(self):
        translations = {
            "pt-br": "https://site.com/artigo",
            "es": "https://site.com/es/articulo",
        }
        schema = generate_hreflang_schema(translations)
        assert len(schema) == 2
        assert schema[0]["inLanguage"] == "pt-BR"

    def test_language_config(self):
        config = get_language_config("pt-br")
        assert config["hreflang"] == "pt-br"
        assert config["serp_gl"] == "br"

    def test_language_config_fallback(self):
        config = get_language_config("unknown")
        assert config["hreflang"] == "pt-br"  # defaults to PT-BR

    def test_all_configs_present(self):
        for lang in ["pt-br", "en", "es"]:
            assert lang in LANGUAGE_CONFIGS


# === Story 7.5 — API (basic import test) ===

class TestAPIImport:

    def test_app_imports(self):
        """Verify FastAPI app can be imported without errors."""
        try:
            from api.app import app
            assert app.title == "Fabrica de Artigos SEO — API"
        except ImportError:
            # FastAPI not installed — skip gracefully
            pytest.skip("FastAPI not installed")
