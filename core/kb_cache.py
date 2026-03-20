"""KnowledgeBaseCache — In-memory cache for KB content with TTL."""
import time
from core.knowledge_base import KnowledgeBase
from core.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseCache:
    """Caches KB content to avoid reloading per-agent (was 4x per keyword)."""

    def __init__(self, ttl=3600):
        """
        Args:
            ttl: Time-to-live in seconds (default: 1 hour).
        """
        self._cache = {}  # {cache_key: (content, timestamp)}
        self._ttl = ttl
        self._hits = 0
        self._misses = 0

    def get(self, tenant_id, kb_path, file_filter=None):
        """Get KB content from cache or load from disk.

        Args:
            tenant_id: Tenant identifier for cache key.
            kb_path: Path to knowledge_base directory.
            file_filter: List of filename substrings to filter.

        Returns:
            KB content string.
        """
        filter_key = str(sorted(file_filter)) if file_filter else "all"
        cache_key = f"{tenant_id}:{filter_key}"

        # Check cache
        if cache_key in self._cache:
            content, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._ttl:
                self._hits += 1
                logger.debug("KB cache HIT: %s", cache_key)
                return content
            else:
                # Expired
                del self._cache[cache_key]
                logger.debug("KB cache EXPIRED: %s", cache_key)

        # Cache miss — load from disk
        self._misses += 1
        logger.debug("KB cache MISS: %s — loading from %s", cache_key, kb_path)
        kb = KnowledgeBase(kb_path)
        content = kb.load(file_filter=file_filter)
        self._cache[cache_key] = (content, time.time())
        return content

    def get_voice_guide(self, tenant_id, kb_path):
        """Get voice guide from cache or load from disk.

        Args:
            tenant_id: Tenant identifier.
            kb_path: Path to knowledge_base directory.

        Returns:
            Voice guide content string.
        """
        cache_key = f"{tenant_id}:voice_guide"

        if cache_key in self._cache:
            content, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._ttl:
                self._hits += 1
                return content
            else:
                del self._cache[cache_key]

        self._misses += 1
        kb = KnowledgeBase(kb_path)
        content = kb.load_voice_guide()
        self._cache[cache_key] = (content, time.time())
        return content

    def invalidate(self, tenant_id):
        """Remove all cached entries for a tenant."""
        keys_to_remove = [k for k in self._cache if k.startswith(f"{tenant_id}:")]
        for key in keys_to_remove:
            del self._cache[key]
        if keys_to_remove:
            logger.info("KB cache invalidated for tenant '%s' (%d entries)", tenant_id, len(keys_to_remove))

    def clear(self):
        """Clear all cached entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info("KB cache cleared (%d entries)", count)

    @property
    def stats(self):
        """Return cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total": total,
            "hit_rate": f"{hit_rate:.1f}%",
            "entries": len(self._cache),
        }
