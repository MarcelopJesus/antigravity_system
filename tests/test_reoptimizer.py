"""Tests for ArticleReoptimizer."""
import unittest
from unittest.mock import MagicMock


class TestReoptimizer(unittest.TestCase):

    def _make_reoptimizer(self):
        from core.reoptimizer import ArticleReoptimizer
        wp = MagicMock()
        config = {
            "wordpress_url": "https://example.com",
            "author_name": "Test Author",
            "business_name": "Test Business",
            "address": "123 Main St",
            "phone": "+1234",
            "geo_lat": "-23.6",
            "geo_lng": "-46.6",
        }
        return ArticleReoptimizer(wp, config)

    def test_analyze_and_fix_no_schema_in_content(self):
        """Schema should NOT be in content (WordPress renders it as text)."""
        opt = self._make_reoptimizer()
        html = "<h1>Test</h1><p>Content here.</p>"
        fixed, meta = opt.analyze_and_fix(html, "test keyword", "Test Title")
        assert 'application/ld+json' not in fixed
        assert '"Article"' not in fixed

    def test_analyze_and_fix_fixes_empty_alt(self):
        opt = self._make_reoptimizer()
        html = '<img src="test.jpg" alt="">'
        fixed, meta = opt.analyze_and_fix(html, "keyword", "Title")
        assert 'alt="keyword - Title"' in fixed

    def test_analyze_and_fix_fixes_missing_alt(self):
        opt = self._make_reoptimizer()
        html = '<img src="test.jpg">'
        fixed, meta = opt.analyze_and_fix(html, "keyword", "Title")
        assert 'alt="keyword - Title"' in fixed

    def test_analyze_and_fix_preserves_good_alt(self):
        opt = self._make_reoptimizer()
        html = '<img src="test.jpg" alt="Good descriptive alt text">'
        fixed, meta = opt.analyze_and_fix(html, "keyword", "Title")
        assert 'alt="Good descriptive alt text"' in fixed

    def test_analyze_and_fix_generates_excerpt(self):
        opt = self._make_reoptimizer()
        html = "<p>First sentence here. Second sentence here. Third.</p>"
        fixed, meta = opt.analyze_and_fix(html, "kw", "T")
        assert 'excerpt' in meta
        assert "First sentence here." in meta['excerpt']

    def test_removes_existing_schema_from_content(self):
        """Any existing schema in content should be stripped out."""
        opt = self._make_reoptimizer()
        html = '<script type="application/ld+json">{"old": true}</script><p>Content</p>'
        fixed, meta = opt.analyze_and_fix(html, "kw", "T")
        assert '"old"' not in fixed
        assert 'application/ld+json' not in fixed
        assert '<p>Content</p>' in fixed

    def test_reoptimize_all(self):
        opt = self._make_reoptimizer()
        opt.wp.get_posts.return_value = [
            {
                'id': 1,
                'title': {'rendered': 'Post 1'},
                'content': {'rendered': '<p>Hello world. Test content.</p>'},
                'slug': 'post-1',
                'featured_media': 10,
            }
        ]
        opt.wp.update_post.return_value = {'id': 1}
        opt.wp.update_media.return_value = True

        results = opt.reoptimize_all()
        assert len(results) == 1
        assert results[0]['success'] is True
        opt.wp.update_post.assert_called_once()
        opt.wp.update_media.assert_called_once()


if __name__ == "__main__":
    unittest.main()
