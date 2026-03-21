"""Tests for Story 7.3 — SEO Scoring Agent."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agents.seo_scorer import SeoScorer, SeoScore, SeoCheck, _check_heading_hierarchy, _compute_grade


# A well-optimized article fixture
GOOD_HTML = """
<h1>Ansiedade Generalizada: O Que a TRI Revela</h1>
<!-- IMG_PLACEHOLDER -->
<p>A ansiedade generalizada é uma condição emocional que afeta milhões de brasileiros.
Neste artigo, vamos entender como a ansiedade se manifesta e o que pode ser feito.</p>
<h2>O Que É Ansiedade Generalizada</h2>
<p>A ansiedade generalizada se caracteriza por preocupação excessiva e persistente.
É importante entender que a ansiedade é uma resposta natural do corpo.</p>
<h3>Sintomas Comuns</h3>
<p>Os sintomas incluem tensão muscular, dificuldade de concentração e insônia.
A ansiedade pode se manifestar de formas diferentes em cada pessoa.</p>
<h2>A Perspectiva da TRI</h2>
<p>A Terapia de Reintegração Implícita entende que a ansiedade não é um defeito,
mas uma adaptação do corpo a situações de conflito interno. A ansiedade generalizada
é vista como um padrão de resposta que pode ser trabalhado de forma breve e direta.</p>
<h3>Como a TRI Aborda a Ansiedade</h3>
<p>Na TRI, trabalhamos diretamente com o conflito visceral que sustenta a ansiedade.
Isso significa que não tentamos controlar os sintomas, mas resolver a causa.</p>
<h2>O Que Fazer</h2>
<p>O primeiro passo é entender que sua ansiedade tem uma função. Ela está tentando
protegê-lo de algo. A terapia pode ajudar a identificar e resolver esse conflito.</p>
<a href="https://example.com/tri">Saiba mais sobre TRI</a>
<a href="https://example.com/terapia">Terapia online</a>
<!-- IMG_PLACEHOLDER -->
<div class="cta-box">
   <p>Quer entender melhor o que está por trás do que você sente? Agende uma avaliação.</p>
   <a href="https://wa.me/message/YT55SSBKHM4DC1" class="btn-whatsapp" target="_blank" rel="noopener">→ Falar com Marcelo Jesus no WhatsApp</a>
</div>
""" + (" palavra" * 950)  # pad to >1000 words


class TestSeoScorer:
    """Test individual SEO checks."""

    @pytest.fixture
    def scorer(self):
        return SeoScorer()

    def test_keyword_in_title_pass(self, scorer):
        html = "<h1>Ansiedade Generalizada</h1><p>content</p>"
        result = scorer.score(html, "ansiedade generalizada", "meta desc here 120+ chars" + "x" * 100)
        check = next(c for c in result.checks if c.name == "keyword_in_title")
        assert check.passed
        assert check.score == 12

    def test_keyword_in_title_fail(self, scorer):
        html = "<h1>Outro Título</h1><p>content</p>"
        result = scorer.score(html, "ansiedade", "meta")
        check = next(c for c in result.checks if c.name == "keyword_in_title")
        assert not check.passed
        assert check.score == 0

    def test_keyword_in_first_paragraph_pass(self, scorer):
        html = "<h1>Title</h1><p>A ansiedade é uma condição que afeta muitas pessoas.</p>"
        result = scorer.score(html, "ansiedade", "meta")
        check = next(c for c in result.checks if c.name == "keyword_in_first_paragraph")
        assert check.passed

    def test_keyword_in_first_paragraph_fail(self, scorer):
        html = "<h1>Title</h1>" + "<p>Lorem ipsum dolor sit amet.</p>" * 20 + "<p>ansiedade aqui</p>"
        result = scorer.score(html, "ansiedade", "meta")
        check = next(c for c in result.checks if c.name == "keyword_in_first_paragraph")
        # The keyword appears far past 300 chars
        assert not check.passed

    def test_h1_unique_pass(self, scorer):
        html = "<h1>Single Title</h1><h2>Section</h2>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "h1_unique")
        assert check.passed

    def test_h1_unique_fail_multiple(self, scorer):
        html = "<h1>Title One</h1><h1>Title Two</h1>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "h1_unique")
        assert not check.passed

    def test_h1_unique_fail_none(self, scorer):
        html = "<h2>No H1</h2><p>content</p>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "h1_unique")
        assert not check.passed

    def test_heading_hierarchy_pass(self, scorer):
        html = "<h1>T</h1><h2>S</h2><h3>SS</h3><h2>S2</h2>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "heading_hierarchy")
        assert check.passed

    def test_heading_hierarchy_fail_skip(self, scorer):
        html = "<h1>T</h1><h3>Skipped H2</h3>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "heading_hierarchy")
        assert not check.passed

    def test_meta_description_length_ideal(self, scorer):
        meta = "A" * 130  # 130 chars, within 120-155
        result = scorer.score("<h1>T</h1><p>c</p>", "test", meta)
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert check.passed
        assert check.score == 8

    def test_meta_description_length_acceptable(self, scorer):
        meta = "A" * 110  # 110 chars, within 100-119
        result = scorer.score("<h1>T</h1><p>c</p>", "test", meta)
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert not check.passed  # passed = ideal only
        assert check.score == 5

    def test_meta_description_length_marginal(self, scorer):
        meta = "A" * 160  # 160 chars, within 156-165
        result = scorer.score("<h1>T</h1><p>c</p>", "test", meta)
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert not check.passed
        assert check.score == 3

    def test_meta_description_length_156_not_zero(self, scorer):
        """Regression: 156 chars should score 3, not 0."""
        meta = "A" * 156
        result = scorer.score("<h1>T</h1><p>c</p>", "test", meta)
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert check.score == 3  # was 0 before fix

    def test_meta_description_length_fail_short(self, scorer):
        result = scorer.score("<h1>T</h1><p>c</p>", "test", "too short")
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert not check.passed
        assert check.score == 0

    def test_meta_description_length_fail_very_long(self, scorer):
        result = scorer.score("<h1>T</h1><p>c</p>", "test", "A" * 200)
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert not check.passed
        assert check.score == 0

    def test_meta_description_boundary_155(self, scorer):
        meta = "A" * 155  # upper boundary of ideal
        result = scorer.score("<h1>T</h1><p>c</p>", "test", meta)
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert check.score == 8

    def test_meta_description_boundary_165(self, scorer):
        meta = "A" * 165  # upper boundary of marginal
        result = scorer.score("<h1>T</h1><p>c</p>", "test", meta)
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert check.score == 3

    def test_meta_description_boundary_166(self, scorer):
        meta = "A" * 166  # just above marginal → 0
        result = scorer.score("<h1>T</h1><p>c</p>", "test", meta)
        check = next(c for c in result.checks if c.name == "meta_description_length")
        assert check.score == 0

    def test_keyword_density_pass(self, scorer):
        # ~1.5% density: keyword appears ~15 times in 1000 words
        words = ["palavra"] * 985 + ["ansiedade"] * 15
        text = " ".join(words)
        html = f"<h1>Ansiedade</h1><p>{text}</p>"
        result = scorer.score(html, "ansiedade", "meta")
        check = next(c for c in result.checks if c.name == "keyword_density")
        assert check.passed

    def test_keyword_density_fail_too_low(self, scorer):
        words = ["palavra"] * 999 + ["ansiedade"] * 1
        text = " ".join(words)
        html = f"<h1>T</h1><p>{text}</p>"
        result = scorer.score(html, "ansiedade", "meta")
        check = next(c for c in result.checks if c.name == "keyword_density")
        assert not check.passed

    def test_internal_links_pass(self, scorer):
        html = '<h1>T</h1><p>c</p><a href="http://a.com">a</a><a href="http://b.com">b</a>'
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "internal_links")
        assert check.passed

    def test_internal_links_fail(self, scorer):
        html = "<h1>T</h1><p>No links here.</p>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "internal_links")
        assert not check.passed

    def test_images_pass_placeholder(self, scorer):
        html = "<h1>T</h1><!-- IMG_PLACEHOLDER --><p>c</p>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "images")
        assert check.passed

    def test_images_pass_img_tag(self, scorer):
        html = '<h1>T</h1><img src="photo.jpg"><p>c</p>'
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "images")
        assert check.passed

    def test_images_fail(self, scorer):
        html = "<h1>T</h1><p>no images</p>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "images")
        assert not check.passed

    def test_word_count_pass(self, scorer):
        text = " ".join(["palavra"] * 1100)
        html = f"<h1>T</h1><p>{text}</p>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "word_count")
        assert check.passed

    def test_word_count_fail(self, scorer):
        html = "<h1>T</h1><p>Short article.</p>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "word_count")
        assert not check.passed

    def test_cta_present_pass(self, scorer):
        html = '<h1>T</h1><p>c</p><div class="cta-box"><p>CTA</p></div>'
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "cta_present")
        assert check.passed

    def test_cta_present_fail(self, scorer):
        html = "<h1>T</h1><p>No CTA</p>"
        result = scorer.score(html, "test", "meta")
        check = next(c for c in result.checks if c.name == "cta_present")
        assert not check.passed


class TestSeoGrade:
    """Test grade computation."""

    def test_grade_a(self):
        assert _compute_grade(70) == "A"
        assert _compute_grade(100) == "A"

    def test_grade_b(self):
        assert _compute_grade(50) == "B"
        assert _compute_grade(69) == "B"

    def test_grade_c(self):
        assert _compute_grade(40) == "C"
        assert _compute_grade(49) == "C"

    def test_grade_d(self):
        assert _compute_grade(0) == "D"
        assert _compute_grade(39) == "D"


class TestHeadingHierarchy:
    """Test heading hierarchy validation."""

    def test_valid_hierarchy(self):
        assert _check_heading_hierarchy(["h1", "h2", "h3", "h2", "h3"]) is True

    def test_empty(self):
        assert _check_heading_hierarchy([]) is True

    def test_skip_level(self):
        assert _check_heading_hierarchy(["h1", "h3"]) is False

    def test_going_up_is_ok(self):
        assert _check_heading_hierarchy(["h1", "h2", "h3", "h2"]) is True


class TestSeoScorerIntegration:
    """Test the scorer with a full well-optimized article."""

    def test_good_article_scores_well(self):
        scorer = SeoScorer()
        result = scorer.score(
            html=GOOD_HTML,
            keyword="ansiedade generalizada",
            meta_description="Entenda o que é ansiedade generalizada e como a TRI pode ajudar. Descubra uma abordagem breve e eficaz para lidar com a ansiedade.",
            title="Ansiedade Generalizada: O Que a TRI Revela",
            lsi_keywords=["terapia", "tratamento", "sintomas", "emocional", "conflito"],
            slug="ansiedade-generalizada-tri",
            entities=["ansiedade", "TRI", "terapia"],
        )
        assert result.total >= 50  # Should score at least B with new checks
        assert result.grade in ("A", "B")
        assert len(result.checks) == 15

    def test_all_checks_present(self):
        scorer = SeoScorer()
        result = scorer.score("<h1>T</h1><p>c</p>", "test", "meta")
        check_names = {c.name for c in result.checks}
        expected = {
            "keyword_in_title", "keyword_in_first_paragraph", "h1_unique",
            "heading_hierarchy", "meta_description_length", "keyword_density",
            "internal_links", "images", "word_count", "cta_present",
            "readability", "semantic_coverage", "entity_coverage",
            "slug_optimization", "outbound_links",
        }
        assert check_names == expected

    def test_max_score_is_100(self):
        scorer = SeoScorer()
        result = scorer.score("<h1>T</h1><p>c</p>", "test", "meta")
        total_max = sum(c.max_score for c in result.checks)
        assert total_max == 100


class TestSemanticCoverage:
    """Test semantic coverage check (Story 2.2)."""

    @pytest.fixture
    def scorer(self):
        return SeoScorer()

    def test_high_coverage(self, scorer):
        text = " ".join(["palavra"] * 500)
        html = f"<h1>Test</h1><p>terapia tratamento sintomas emocional conflito {text}</p>"
        result = scorer.score(html, "test", lsi_keywords=["terapia", "tratamento", "sintomas", "emocional", "conflito"])
        check = next(c for c in result.checks if c.name == "semantic_coverage")
        assert check.score == 5

    def test_partial_coverage(self, scorer):
        text = " ".join(["palavra"] * 500)
        html = f"<h1>Test</h1><p>terapia tratamento {text}</p>"
        result = scorer.score(html, "test", lsi_keywords=["terapia", "tratamento", "sintomas", "emocional", "conflito"])
        check = next(c for c in result.checks if c.name == "semantic_coverage")
        assert check.score == 3  # 2/5 = 40%

    def test_low_coverage(self, scorer):
        text = " ".join(["palavra"] * 500)
        html = f"<h1>Test</h1><p>terapia {text}</p>"
        result = scorer.score(html, "test", lsi_keywords=["terapia", "tratamento", "sintomas", "emocional", "conflito"])
        check = next(c for c in result.checks if c.name == "semantic_coverage")
        assert check.score == 0  # 1/5 = 20%

    def test_no_lsi_keywords(self, scorer):
        html = "<h1>Test</h1><p>content</p>"
        result = scorer.score(html, "test")
        check = next(c for c in result.checks if c.name == "semantic_coverage")
        assert check.score == 0


class TestSlugOptimization:
    """Test slug optimization check (Story 2.4)."""

    @pytest.fixture
    def scorer(self):
        return SeoScorer()

    def test_good_slug(self, scorer):
        html = "<h1>Test</h1><p>content</p>"
        result = scorer.score(html, "ansiedade generalizada", slug="ansiedade-generalizada-tratamento")
        check = next(c for c in result.checks if c.name == "slug_optimization")
        assert check.score == 5

    def test_slug_with_stop_words(self, scorer):
        html = "<h1>Test</h1><p>content</p>"
        result = scorer.score(html, "ansiedade", slug="ansiedade-e-o-que-fazer-para-melhorar")
        check = next(c for c in result.checks if c.name == "slug_optimization")
        assert check.score == 3  # keyword present but has stop words

    def test_slug_without_keyword(self, scorer):
        html = "<h1>Test</h1><p>content</p>"
        result = scorer.score(html, "ansiedade", slug="como-melhorar-saude-mental")
        check = next(c for c in result.checks if c.name == "slug_optimization")
        assert check.score == 0

    def test_no_slug(self, scorer):
        html = "<h1>Test</h1><p>content</p>"
        result = scorer.score(html, "test")
        check = next(c for c in result.checks if c.name == "slug_optimization")
        assert check.score == 0


class TestOutboundLinks:
    """Test outbound links check (Story 2.5)."""

    @pytest.fixture
    def scorer(self):
        return SeoScorer()

    def test_two_authoritative_links(self, scorer):
        html = '<h1>T</h1><p>Segundo a <a href="https://pubmed.ncbi.nlm.nih.gov/123">pesquisa</a> e dados da <a href="https://www.who.int/news">OMS</a>.</p>'
        result = scorer.score(html, "test")
        check = next(c for c in result.checks if c.name == "outbound_links")
        assert check.score == 2

    def test_one_authoritative_link(self, scorer):
        html = '<h1>T</h1><p>Segundo a <a href="https://pt.wikipedia.org/wiki/Ansiedade">Wikipedia</a>.</p>'
        result = scorer.score(html, "test")
        check = next(c for c in result.checks if c.name == "outbound_links")
        assert check.score == 1

    def test_only_cta_links_not_counted(self, scorer):
        html = '<h1>T</h1><p>c</p><a href="https://wa.me/123">WhatsApp</a><a href="https://instagram.com/test">IG</a>'
        result = scorer.score(html, "test")
        check = next(c for c in result.checks if c.name == "outbound_links")
        assert check.score == 0

    def test_no_links(self, scorer):
        html = "<h1>T</h1><p>No links here.</p>"
        result = scorer.score(html, "test")
        check = next(c for c in result.checks if c.name == "outbound_links")
        assert check.score == 0
