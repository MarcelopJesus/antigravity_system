"""Tests for Story 5.1 — Google Search Console Client."""
import pytest
from unittest.mock import patch, MagicMock
from core.integrations.gsc_client import (
    find_page2_opportunities, compare_periods,
)


class TestFindPage2Opportunities:

    @patch("core.integrations.gsc_client.get_article_performance")
    def test_finds_page2_articles(self, mock_perf):
        mock_perf.return_value = [
            {"page": "https://example.com/a", "clicks": 5, "impressions": 100, "ctr": 5.0, "position": 15.0},
            {"page": "https://example.com/b", "clicks": 10, "impressions": 200, "ctr": 5.0, "position": 5.0},
            {"page": "https://example.com/c", "clicks": 3, "impressions": 150, "ctr": 2.0, "position": 12.0},
        ]
        result = find_page2_opportunities("https://example.com")
        assert len(result) == 2  # a (pos 15) and c (pos 12)
        assert result[0]["page"].endswith("/c")  # sorted by impressions desc

    @patch("core.integrations.gsc_client.get_article_performance")
    def test_no_opportunities(self, mock_perf):
        mock_perf.return_value = [
            {"page": "https://example.com/a", "clicks": 10, "impressions": 200, "ctr": 5.0, "position": 3.0},
        ]
        result = find_page2_opportunities("https://example.com")
        assert len(result) == 0


class TestComparePeriods:

    @patch("core.integrations.gsc_client.get_article_performance")
    def test_detects_decline(self, mock_perf):
        # First call = current, second call = previous (longer period)
        mock_perf.side_effect = [
            [{"page": "https://example.com/a", "clicks": 5, "impressions": 100, "ctr": 5.0, "position": 20.0}],
            [{"page": "https://example.com/a", "clicks": 10, "impressions": 200, "ctr": 5.0, "position": 8.0}],
        ]
        changes = compare_periods("https://example.com")
        assert len(changes) == 1
        assert changes[0]["status"] == "declined"
        assert changes[0]["change"] < 0

    @patch("core.integrations.gsc_client.get_article_performance")
    def test_detects_improvement(self, mock_perf):
        mock_perf.side_effect = [
            [{"page": "https://example.com/a", "clicks": 10, "impressions": 200, "ctr": 5.0, "position": 3.0}],
            [{"page": "https://example.com/a", "clicks": 5, "impressions": 100, "ctr": 5.0, "position": 10.0}],
        ]
        changes = compare_periods("https://example.com")
        assert len(changes) == 1
        assert changes[0]["status"] == "improved"

    @patch("core.integrations.gsc_client.get_article_performance")
    def test_empty_data(self, mock_perf):
        mock_perf.return_value = []
        assert compare_periods("https://example.com") == []
