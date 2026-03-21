"""Tests for Story 2.3 — Entity Coverage Check."""
import pytest
from core.seo.entity_checker import check_entity_coverage


class TestEntityCoverage:

    def test_all_entities_found(self):
        text = "A ansiedade é tratada por psicólogo com terapia cognitiva."
        entities = ["ansiedade", "psicólogo", "terapia cognitiva"]
        result = check_entity_coverage(text, entities)
        assert result["found"] == 3
        assert result["ratio"] == 1.0
        assert result["missing"] == []

    def test_partial_coverage(self):
        text = "A ansiedade é um problema comum."
        entities = ["ansiedade", "psicólogo", "serotonina"]
        result = check_entity_coverage(text, entities)
        assert result["found"] == 1
        assert len(result["missing"]) == 2

    def test_no_entities_found(self):
        text = "O sol brilha no céu azul."
        entities = ["ansiedade", "terapia"]
        result = check_entity_coverage(text, entities)
        assert result["found"] == 0
        assert result["ratio"] == 0.0

    def test_empty_entities_list(self):
        result = check_entity_coverage("text", [])
        assert result["found"] == 0
        assert result["total"] == 0

    def test_case_insensitive(self):
        text = "A OMS publicou dados sobre ANSIEDADE."
        entities = ["oms", "ansiedade"]
        result = check_entity_coverage(text, entities)
        assert result["found"] == 2
