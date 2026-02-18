"""Tests for Story 7.1 — Internal Linking Enforcement."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.seo.internal_links import inject_internal_links


class TestInjectInternalLinks:
    """Tests for inject_internal_links function."""

    def test_basic_link_insertion(self):
        html = "<p>A ansiedade é uma resposta natural do corpo.</p>"
        strategy = [{"text": "ansiedade", "url": "https://example.com/ansiedade"}]
        result, count = inject_internal_links(html, strategy)
        assert count == 1
        assert '<a href="https://example.com/ansiedade">ansiedade</a>' in result

    def test_no_strategy_returns_unchanged(self):
        html = "<p>Hello world</p>"
        result, count = inject_internal_links(html, [])
        assert result == html
        assert count == 0

    def test_empty_html_returns_unchanged(self):
        result, count = inject_internal_links("", [{"text": "test", "url": "http://x.com"}])
        assert result == ""
        assert count == 0

    def test_max_links_respected(self):
        html = "<p>Tema um. Tema dois. Tema três. Tema quatro.</p>"
        strategy = [
            {"text": "Tema um", "url": "http://1.com"},
            {"text": "Tema dois", "url": "http://2.com"},
            {"text": "Tema três", "url": "http://3.com"},
            {"text": "Tema quatro", "url": "http://4.com"},
        ]
        result, count = inject_internal_links(html, strategy, max_links=2)
        assert count <= 2

    def test_skips_text_inside_headings(self):
        html = "<h2>Ansiedade Generalizada</h2><p>A ansiedade é comum.</p>"
        strategy = [{"text": "Ansiedade Generalizada", "url": "http://x.com"}]
        result, count = inject_internal_links(html, strategy)
        # Should NOT link inside the H2
        assert '<h2><a href' not in result

    def test_skips_already_linked_text(self):
        html = '<p>Veja sobre <a href="http://old.com">terapia TRI</a> aqui.</p>'
        strategy = [{"text": "terapia TRI", "url": "http://new.com"}]
        result, count = inject_internal_links(html, strategy)
        # Should not double-link
        assert 'http://new.com' not in result

    def test_case_insensitive_matching(self):
        html = "<p>A ANSIEDADE pode ser tratada.</p>"
        strategy = [{"text": "ansiedade", "url": "http://x.com"}]
        result, count = inject_internal_links(html, strategy)
        assert count == 1
        assert '<a href="http://x.com">ANSIEDADE</a>' in result

    def test_missing_text_or_url_skipped(self):
        html = "<p>Some text here.</p>"
        strategy = [
            {"text": "", "url": "http://x.com"},
            {"text": "Some text", "url": ""},
            {"url": "http://x.com"},
        ]
        result, count = inject_internal_links(html, strategy)
        assert count == 0

    def test_partial_match_fallback(self):
        html = "<p>A terapia cognitiva comportamental é eficaz.</p>"
        strategy = [{"text": "terapia cognitiva comportamental avançada", "url": "http://x.com"}]
        result, count = inject_internal_links(html, strategy)
        # Should try partial "terapia cognitiva" match
        assert count == 1
        assert '<a href="http://x.com">' in result

    def test_multiple_links_inserted(self):
        html = "<p>A ansiedade e a depressão são condições comuns.</p>"
        strategy = [
            {"text": "ansiedade", "url": "http://a.com"},
            {"text": "depressão", "url": "http://d.com"},
        ]
        result, count = inject_internal_links(html, strategy)
        assert count == 2
        assert '<a href="http://a.com">' in result
        assert '<a href="http://d.com">' in result
