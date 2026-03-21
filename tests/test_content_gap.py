"""Tests for Story 3.3 — Content Gap Analyzer."""
import pytest
from core.seo.content_gap import find_content_gaps


MOCK_SERP_BRIEF = {
    "related_searches": [
        "ansiedade generalizada tratamento natural",
        "ansiedade generalizada sintomas físicos",
        "como controlar ansiedade",
    ],
    "people_also_ask": [
        {"question": "Ansiedade generalizada tem cura?"},
        {"question": "Quais os sintomas da ansiedade?"},
    ],
}


class TestContentGap:

    def test_finds_gaps(self):
        existing = ["ansiedade generalizada"]
        gaps = find_content_gaps(MOCK_SERP_BRIEF, existing)
        assert len(gaps) > 0
        keywords = [g["keyword"] for g in gaps]
        assert "como controlar ansiedade" in keywords

    def test_no_gaps_when_all_covered(self):
        existing = [
            "ansiedade generalizada tratamento natural",
            "ansiedade generalizada sintomas físicos",
            "como controlar ansiedade",
            "Ansiedade generalizada tem cura?",
            "Quais os sintomas da ansiedade?",
        ]
        gaps = find_content_gaps(MOCK_SERP_BRIEF, existing)
        assert len(gaps) == 0

    def test_case_insensitive(self):
        existing = ["COMO CONTROLAR ANSIEDADE"]
        gaps = find_content_gaps(MOCK_SERP_BRIEF, existing)
        keywords = [g["keyword"].lower() for g in gaps]
        assert "como controlar ansiedade" not in keywords

    def test_empty_serp_brief(self):
        assert find_content_gaps({}, ["test"]) == []
        assert find_content_gaps(None, ["test"]) == []

    def test_source_tagging(self):
        gaps = find_content_gaps(MOCK_SERP_BRIEF, [])
        sources = {g["source"] for g in gaps}
        assert "related_search" in sources
        assert "people_also_ask" in sources
