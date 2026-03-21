"""Tests for Story 2.1 — Readability Score (PT-BR)."""
import pytest
from core.seo.readability import count_syllables_pt, readability_score_pt


class TestCountSyllablesPt:
    """Test syllable counting for Portuguese words."""

    def test_single_syllable(self):
        assert count_syllables_pt("sol") == 1
        assert count_syllables_pt("mar") == 1

    def test_two_syllables(self):
        assert count_syllables_pt("casa") == 2
        assert count_syllables_pt("mesa") == 2

    def test_three_syllables(self):
        assert count_syllables_pt("bonito") == 3
        assert count_syllables_pt("cadeira") == 3  # ca-dei-ra (ei = diphthong)

    def test_diphthongs_count_as_one(self):
        # "pai" has diphthong "ai" → 1 syllable
        assert count_syllables_pt("pai") == 1
        # "noite" has diphthong "oi" → 2 syllables (noi-te)
        assert count_syllables_pt("noite") == 2

    def test_accented_vowels(self):
        assert count_syllables_pt("café") == 2
        assert count_syllables_pt("saúde") == 3  # sa-ú-de

    def test_empty_word(self):
        assert count_syllables_pt("") == 0

    def test_minimum_one_syllable(self):
        assert count_syllables_pt("x") >= 1


class TestReadabilityScorePt:
    """Test readability index calculation."""

    def test_easy_text(self):
        # Short sentences, simple words
        text = "O sol brilha. A casa é bonita. O dia está bom. " * 20
        result = readability_score_pt(text)
        assert result["level"] in ("facil", "muito_facil")
        assert result["index"] >= 50

    def test_hard_text(self):
        # Long sentences, complex words
        text = (
            "A implementação de metodologias interdisciplinares contemporâneas "
            "proporciona significativamente a potencialização das habilidades "
            "sociocognitivas fundamentais para o desenvolvimento profissional "
            "e a consolidação epistemológica das estruturas organizacionais. "
        ) * 10
        result = readability_score_pt(text)
        assert result["level"] in ("dificil", "medio")
        assert result["index"] < 50

    def test_empty_text(self):
        result = readability_score_pt("")
        assert result["index"] == 0.0
        assert result["level"] == "indefinido"

    def test_returns_all_fields(self):
        result = readability_score_pt("Uma frase simples. Outra frase.")
        assert "index" in result
        assert "level" in result
        assert "asl" in result
        assert "asw" in result
        assert "sentence_count" in result
        assert "word_count" in result

    def test_sentence_count(self):
        result = readability_score_pt("Frase um. Frase dois. Frase três.")
        assert result["sentence_count"] == 3

    def test_index_clamped_0_100(self):
        result = readability_score_pt("A. B. C. D. E.")
        assert 0 <= result["index"] <= 100
