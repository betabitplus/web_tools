"""Web Tools Cache Manager.

URL-keyed cache using the shared cache infrastructure for storing crawl results.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from py_lib_runtime import BaseCacheManager, resolve_cache_dir

from web_tools._internal.config import get_default_web_tools_resolver


@dataclass
class CacheEntry:
    """Cached crawl result for a URL."""

    url: str
    html: str
    mhtml: str | None = None
    screenshot: bytes | None = None
    timestamp: str | None = None


class CacheManager(BaseCacheManager[CacheEntry]):
    """URL-keyed cache manager for web crawl results.

    Provides automatic LRU eviction when cache exceeds size limit.
    Thread-safe and process-safe by default.

    Example:
        >>> cache = CacheManager(cache_dir=Path("/tmp/web_tools_cache"))
        >>> cache.set("https://example.com", CacheEntry(url="...", html="..."))
        >>> entry = cache.get("https://example.com")
        >>> cache.has("https://example.com")
        True
    """

    def __init__(
        self,
        cache_dir: Path,
        max_size: int | None = None,
        compression_threshold: int | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage
            max_size: Maximum cache size in bytes (defaults to config)
            compression_threshold: Minimum size in bytes to compress values
            ttl_seconds: Time-to-live in seconds for entries (default: disabled)
        """
        default_max_size = (
            get_default_web_tools_resolver().defaults.cache_max_size_bytes
        )
        config_max_size = max_size if max_size is not None else default_max_size
        super().__init__(
            cache_dir=cache_dir,
            max_size=config_max_size,
            compression_threshold=compression_threshold,
            ttl_seconds=ttl_seconds,
        )

    def _serialize_entry(self, entry: CacheEntry) -> dict:
        """Convert CacheEntry to dict for storage."""
        return {
            "url": entry.url,
            "html": entry.html,
            "mhtml": entry.mhtml,
            "screenshot": entry.screenshot,
            "timestamp": entry.timestamp,
        }

    def _deserialize_entry(self, data: dict, url: str) -> CacheEntry:
        """Reconstruct CacheEntry from stored dict."""
        return CacheEntry(
            url=data.get("url", url),
            html=data.get("html", ""),
            mhtml=data.get("mhtml"),
            screenshot=data.get("screenshot"),
            timestamp=data.get("timestamp"),
        )


_cache_dir: Path | None = resolve_cache_dir(None, namespace="web_tools")
_cache_instance: CacheManager | None = None


def configure_cache(cache_dir: Path | None) -> None:
    """Configure web tools caching.

    If cache_dir is None, caching is disabled.
    """
    global _cache_dir, _cache_instance  # noqa: PLW0603
    _cache_dir = cache_dir
    if _cache_instance is not None:
        _cache_instance.close()
        _cache_instance = None


def clear_cache_instance() -> None:
    """Close the cached page-cache manager without changing cache configuration."""
    global _cache_instance  # noqa: PLW0603
    if _cache_instance is not None:
        _cache_instance.close()
        _cache_instance = None


def get_cache() -> CacheManager | None:
    """Get the configured cache manager, if caching is configured."""
    global _cache_instance  # noqa: PLW0603
    if _cache_dir is None:
        return None
    if _cache_instance is None:
        _cache_instance = CacheManager(cache_dir=_cache_dir)
    return _cache_instance
