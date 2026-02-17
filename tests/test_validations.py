"""Tests for input/output validation functions (Story 1.5)."""
import pytest
from main import validate_keyword, validate_analyst_output, validate_html_output, clean_orphan_placeholders


class TestValidateKeyword:
    def test_valid_keyword(self):
        is_valid, err = validate_keyword("terapia tri", set())
        assert is_valid is True
        assert err == ""

    def test_empty_keyword(self):
        is_valid, err = validate_keyword("", set())
        assert is_valid is False
        assert "empty" in err.lower()

    def test_none_keyword(self):
        is_valid, err = validate_keyword(None, set())
        assert is_valid is False

    def test_keyword_too_long(self):
        long_kw = "a" * 201
        is_valid, err = validate_keyword(long_kw, set())
        assert is_valid is False
        assert "long" in err.lower()

    def test_duplicate_keyword(self):
        seen = {"terapia tri"}
        is_valid, err = validate_keyword("Terapia TRI", seen)
        assert is_valid is False
        assert "duplicate" in err.lower()

    def test_whitespace_only(self):
        is_valid, err = validate_keyword("   ", set())
        assert is_valid is False


class TestValidateAnalystOutput:
    def test_valid_output(self):
        outline = {
            "title": "Artigo sobre TRI",
            "sections": [{"h2": "Intro"}],
            "meta_description": "Desc"
        }
        is_valid, err = validate_analyst_output(outline)
        assert is_valid is True

    def test_missing_title(self):
        outline = {"sections": [{"h2": "Intro"}]}
        is_valid, err = validate_analyst_output(outline)
        assert is_valid is False
        assert "title" in err.lower()

    def test_missing_sections(self):
        outline = {"title": "Test"}
        is_valid, err = validate_analyst_output(outline)
        assert is_valid is False
        assert "sections" in err.lower()

    def test_empty_title(self):
        outline = {"title": "  ", "sections": []}
        is_valid, err = validate_analyst_output(outline)
        assert is_valid is False
        assert "empty title" in err.lower()

    def test_not_a_dict(self):
        is_valid, err = validate_analyst_output("not a dict")
        assert is_valid is False
        assert "not a valid" in err.lower()

    def test_none_input(self):
        is_valid, err = validate_analyst_output(None)
        assert is_valid is False


class TestValidateHtmlOutput:
    def test_valid_html(self):
        html = "<h2>Title</h2><p>Content here that is long enough to pass validation checks.</p>" * 3
        is_valid, err = validate_html_output(html, "Writer")
        assert is_valid is True

    def test_empty_output(self):
        is_valid, err = validate_html_output("", "Writer")
        assert is_valid is False
        assert "empty" in err.lower()

    def test_none_output(self):
        is_valid, err = validate_html_output(None, "Writer")
        assert is_valid is False

    def test_too_short(self):
        is_valid, err = validate_html_output("<p>Hi</p>", "Writer")
        assert is_valid is False
        assert "short" in err.lower()

    def test_starts_with_markdown(self):
        is_valid, err = validate_html_output("```html\n<h1>Test</h1>" + "x" * 200, "Editor")
        assert is_valid is False
        assert "markdown" in err.lower()

    def test_humanizer_ratio_ok(self):
        original = "<p>" + "word " * 100 + "</p>"
        humanized = "<p>" + "word " * 80 + "</p>"
        is_valid, err = validate_html_output(
            humanized, "Humanizer",
            min_ratio=0.5, reference_len=len(original)
        )
        assert is_valid is True

    def test_humanizer_ratio_too_low(self):
        original = "<p>" + "word " * 200 + "</p>"
        humanized = "<p>" + "word " * 30 + "</p>"
        is_valid, err = validate_html_output(
            humanized, "Humanizer",
            min_ratio=0.5, reference_len=len(original)
        )
        assert is_valid is False
        assert "%" in err


class TestCleanOrphanPlaceholders:
    def test_removes_placeholders(self):
        html = "<p>Before</p><!-- IMG_PLACEHOLDER --><p>After</p>"
        result = clean_orphan_placeholders(html)
        assert "IMG_PLACEHOLDER" not in result
        assert "<p>Before</p><p>After</p>" == result

    def test_no_placeholders(self):
        html = "<p>Clean HTML</p>"
        result = clean_orphan_placeholders(html)
        assert result == html

    def test_multiple_placeholders(self):
        html = "A<!-- IMG_PLACEHOLDER -->B<!-- IMG_PLACEHOLDER -->C"
        result = clean_orphan_placeholders(html)
        assert result == "ABC"
