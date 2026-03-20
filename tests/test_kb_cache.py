"""Tests for KnowledgeBaseCache — caching, TTL, invalidation."""
import pytest
from unittest.mock import patch, MagicMock
from core.kb_cache import KnowledgeBaseCache


class TestKnowledgeBaseCache:
    def setup_method(self):
        self.cache = KnowledgeBaseCache(ttl=3600)

    @patch("core.kb_cache.KnowledgeBase")
    def test_cache_miss_loads_from_disk(self, MockKB):
        mock_kb = MockKB.return_value
        mock_kb.load.return_value = "KB content here"

        content = self.cache.get("mjesus", "/path/to/kb", file_filter=["tri_essencia"])

        assert content == "KB content here"
        assert self.cache.stats["misses"] == 1
        assert self.cache.stats["hits"] == 0
        MockKB.assert_called_once_with("/path/to/kb")

    @patch("core.kb_cache.KnowledgeBase")
    def test_cache_hit_returns_cached(self, MockKB):
        mock_kb = MockKB.return_value
        mock_kb.load.return_value = "KB content"

        # First call = miss
        self.cache.get("mjesus", "/path/to/kb", file_filter=["tri_essencia"])
        # Second call = hit
        content = self.cache.get("mjesus", "/path/to/kb", file_filter=["tri_essencia"])

        assert content == "KB content"
        assert self.cache.stats["hits"] == 1
        assert self.cache.stats["misses"] == 1
        # KB only loaded once
        assert mock_kb.load.call_count == 1

    @patch("core.kb_cache.time.time")
    @patch("core.kb_cache.KnowledgeBase")
    def test_cache_ttl_expiration(self, MockKB, mock_time):
        mock_kb = MockKB.return_value
        mock_kb.load.return_value = "KB content"

        # First call at t=0
        mock_time.return_value = 1000
        self.cache.get("mjesus", "/path/to/kb", file_filter=["tri_essencia"])

        # Second call at t=3601 (expired)
        mock_time.return_value = 4601
        self.cache.get("mjesus", "/path/to/kb", file_filter=["tri_essencia"])

        assert mock_kb.load.call_count == 2  # Reloaded after expiry

    @patch("core.kb_cache.KnowledgeBase")
    def test_invalidate_tenant(self, MockKB):
        mock_kb = MockKB.return_value
        mock_kb.load.return_value = "KB content"

        self.cache.get("mjesus", "/path/to/kb", file_filter=["tri_essencia"])
        self.cache.get("mjesus", "/path/to/kb", file_filter=["premium"])
        assert self.cache.stats["entries"] == 2

        self.cache.invalidate("mjesus")
        assert self.cache.stats["entries"] == 0

    @patch("core.kb_cache.KnowledgeBase")
    def test_clear_all(self, MockKB):
        mock_kb = MockKB.return_value
        mock_kb.load.return_value = "KB content"

        self.cache.get("mjesus", "/path1", file_filter=["a"])
        self.cache.get("clinica", "/path2", file_filter=["b"])
        assert self.cache.stats["entries"] == 2

        self.cache.clear()
        assert self.cache.stats["entries"] == 0

    @patch("core.kb_cache.KnowledgeBase")
    def test_different_filters_separate_entries(self, MockKB):
        mock_kb = MockKB.return_value
        mock_kb.load.side_effect = ["content A", "content B"]

        a = self.cache.get("mjesus", "/path/to/kb", file_filter=["tri_essencia"])
        b = self.cache.get("mjesus", "/path/to/kb", file_filter=["tri_voz"])

        assert a == "content A"
        assert b == "content B"
        assert self.cache.stats["entries"] == 2

    @patch("core.kb_cache.KnowledgeBase")
    def test_voice_guide_caching(self, MockKB):
        mock_kb = MockKB.return_value
        mock_kb.load_voice_guide.return_value = "Voice guide content"

        v1 = self.cache.get_voice_guide("mjesus", "/path/to/kb")
        v2 = self.cache.get_voice_guide("mjesus", "/path/to/kb")

        assert v1 == v2 == "Voice guide content"
        assert mock_kb.load_voice_guide.call_count == 1  # Cached
