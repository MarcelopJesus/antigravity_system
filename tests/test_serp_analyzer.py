"""Tests for Story 3.1 — SERP Analyzer."""
import json
import pytest
from unittest.mock import patch, MagicMock
from core.agents.serp_analyzer import (
    get_serp_data, _parse_serp_response, _estimate_word_count,
    generate_serp_brief,
)


# Mock SerperAPI response
MOCK_SERPER_RESPONSE = {
    "organic": [
        {
            "position": 1,
            "title": "Ansiedade Generalizada: Sintomas e Tratamento",
            "link": "https://example.com/ansiedade",
            "snippet": "A ansiedade generalizada é um transtorno que afeta milhões de pessoas no Brasil. Conheça os sintomas e tratamentos disponíveis.",
        },
        {
            "position": 2,
            "title": "O que é Ansiedade? Causas e Como Tratar",
            "link": "https://example2.com/ansiedade",
            "snippet": "Entenda o que causa a ansiedade e descubra formas eficazes de tratamento.",
        },
    ],
    "peopleAlsoAsk": [
        {"question": "Quais os sintomas da ansiedade generalizada?", "snippet": "Os principais sintomas incluem..."},
        {"question": "Ansiedade generalizada tem cura?", "snippet": "A ansiedade generalizada pode ser tratada..."},
    ],
    "relatedSearches": [
        {"query": "ansiedade generalizada tratamento natural"},
        {"query": "ansiedade generalizada sintomas físicos"},
        {"query": "como controlar ansiedade"},
    ],
}


class TestParseSerpResponse:

    def test_parses_organic_results(self):
        result = _parse_serp_response(MOCK_SERPER_RESPONSE)
        assert len(result["organic"]) == 2
        assert result["organic"][0]["title"] == "Ansiedade Generalizada: Sintomas e Tratamento"
        assert result["organic"][0]["position"] == 1

    def test_parses_people_also_ask(self):
        result = _parse_serp_response(MOCK_SERPER_RESPONSE)
        assert len(result["people_also_ask"]) == 2
        assert "sintomas" in result["people_also_ask"][0]["question"].lower()

    def test_parses_related_searches(self):
        result = _parse_serp_response(MOCK_SERPER_RESPONSE)
        assert len(result["related_searches"]) == 3
        assert "tratamento natural" in result["related_searches"][0]

    def test_empty_response(self):
        result = _parse_serp_response({})
        assert result["organic"] == []
        assert result["people_also_ask"] == []
        assert result["related_searches"] == []


class TestEstimateWordCount:

    def test_normal_snippet(self):
        snippet = "A ansiedade é um problema " + "comum " * 20
        wc = _estimate_word_count(snippet)
        assert 800 <= wc <= 5000

    def test_empty_snippet(self):
        assert _estimate_word_count("") == 1500

    def test_clamped_range(self):
        assert _estimate_word_count("word") >= 800
        long_snippet = " ".join(["word"] * 200)
        assert _estimate_word_count(long_snippet) <= 5000


class TestGetSerpData:

    @patch("core.agents.serp_analyzer.requests.post")
    def test_successful_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SERPER_RESPONSE
        mock_post.return_value = mock_response

        result = get_serp_data("ansiedade", api_key="test-key")
        assert result is not None
        assert len(result["organic"]) == 2

    @patch("core.agents.serp_analyzer.requests.post")
    def test_api_error_returns_none(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        result = get_serp_data("ansiedade", api_key="bad-key")
        assert result is None

    def test_no_api_key_returns_none(self):
        with patch.dict("os.environ", {"SERPER_API_KEY": ""}):
            result = get_serp_data("ansiedade", api_key="")
            assert result is None


class TestGenerateSerpBrief:

    @patch("core.agents.serp_analyzer.get_serp_data")
    def test_generates_full_brief(self, mock_get):
        mock_get.return_value = _parse_serp_response(MOCK_SERPER_RESPONSE)

        brief = generate_serp_brief("ansiedade")
        assert brief["keyword"] == "ansiedade"
        assert len(brief["top_results"]) == 2
        assert len(brief["people_also_ask"]) == 2
        assert len(brief["related_searches"]) == 3
        assert brief["recommended_word_count"] > brief["avg_word_count"]

    @patch("core.agents.serp_analyzer.get_serp_data")
    def test_returns_empty_on_failure(self, mock_get):
        mock_get.return_value = None
        brief = generate_serp_brief("ansiedade")
        assert brief == {}
