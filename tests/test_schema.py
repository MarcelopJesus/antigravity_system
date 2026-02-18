"""Tests for Schema Markup JSON-LD generation."""
import json
import unittest
from core.seo.schema import (
    generate_article_schema,
    generate_local_business_schema,
    generate_faq_schema,
    extract_faq_from_html,
    inject_schema_into_html,
)


class TestArticleSchema(unittest.TestCase):

    def test_generates_valid_json_ld(self):
        result = generate_article_schema(
            title="Test Article",
            description="A test description",
            url="https://example.com/test",
            author_name="John Doe",
            date_published="2026-01-01",
            image_url="https://example.com/img.jpg",
            keyword="test keyword",
        )
        data = json.loads(result)
        assert data["@type"] == "Article"
        assert data["headline"] == "Test Article"
        assert data["author"]["name"] == "John Doe"
        assert data["image"] == "https://example.com/img.jpg"

    def test_no_image_url(self):
        result = generate_article_schema(
            title="T", description="D", url="", author_name="A",
            date_published="2026-01-01", image_url="", keyword="k",
        )
        data = json.loads(result)
        assert "image" not in data


class TestLocalBusinessSchema(unittest.TestCase):

    def test_generates_valid_schema(self):
        result = generate_local_business_schema(
            business_name="Test Biz",
            address="123 Main St",
            phone="+1234567890",
            url="https://example.com",
            geo_lat="-23.6",
            geo_lng="-46.6",
        )
        data = json.loads(result)
        assert data["@type"] == "LocalBusiness"
        assert data["geo"]["latitude"] == "-23.6"

    def test_without_geo(self):
        result = generate_local_business_schema(
            business_name="Test", address="Addr", phone="123", url="",
        )
        data = json.loads(result)
        assert "geo" not in data


class TestFaqSchema(unittest.TestCase):

    def test_generates_faq_schema(self):
        items = [
            {"question": "What is X?", "answer": "X is Y."},
            {"question": "How does Z work?", "answer": "Z works via W."},
        ]
        result = generate_faq_schema(items)
        data = json.loads(result)
        assert data["@type"] == "FAQPage"
        assert len(data["mainEntity"]) == 2

    def test_empty_items(self):
        assert generate_faq_schema([]) == ""

    def test_items_with_missing_fields(self):
        items = [{"question": "Q", "answer": ""}, {"question": "", "answer": "A"}]
        assert generate_faq_schema(items) == ""


class TestExtractFaqFromHtml(unittest.TestCase):

    def test_extracts_faq_items(self):
        html = """
        <h2>FAQ</h2>
        <h3>O que é TRI?</h3>
        <p>TRI é Terapia de Reintegração Implícita.</p>
        <h3>Funciona para ansiedade?</h3>
        <p>Sim, é muito eficaz para ansiedade.</p>
        <h2>Conclusão</h2>
        """
        items = extract_faq_from_html(html)
        assert len(items) == 2
        assert items[0]["question"] == "O que é TRI?"

    def test_no_faq_section(self):
        html = "<h2>Intro</h2><p>Text</p>"
        assert extract_faq_from_html(html) == []


class TestInjectSchema(unittest.TestCase):

    def test_inject_is_noop(self):
        """inject_schema_into_html is now a no-op (WP strips script tags from content)."""
        html = "<h1>Title</h1><p>Content</p>"
        schema = '{"@type": "Article"}'
        result = inject_schema_into_html(html, [schema])
        assert result == html

    def test_no_schemas(self):
        html = "<h1>Title</h1>"
        assert inject_schema_into_html(html, []) == html


if __name__ == "__main__":
    unittest.main()
