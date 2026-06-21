"""Media Cache Manager for web_tools.

URL-keyed cache using the shared cache infrastructure for storing media downloads.
"""

from __future__ import annotations

from pathlib import Path

from py_lib_runtime import BaseCacheManager

from web_tools._api.types import MediaCacheEntry
from web_tools._internal.config import get_default_web_tools_resolver


class MediaCacheManager(BaseCacheManager[MediaCacheEntry]):
    """URL-keyed cache manager for media downloads.

    Provides automatic LRU eviction when cache exceeds size limit.
    Thread-safe and process-safe by default.
    """

    def __init__(
        self,
        cache_dir: Path,
        *,
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
            get_default_web_tools_resolver().defaults.media_cache_max_size_bytes
        )
        config_max_size = max_size if max_size is not None else default_max_size
        super().__init__(
            cache_dir=cache_dir,
            max_size=config_max_size,
            compression_threshold=compression_threshold,
            ttl_seconds=ttl_seconds,
        )

    def _serialize_entry(self, entry: MediaCacheEntry) -> dict:
        """Convert MediaCacheEntry to dict for storage."""
        return {
            "url": entry.url,
            "content": entry.content,
            "content_type": entry.content_type,
            "extension": entry.extension,
            "size_bytes": entry.size_bytes,
            "timestamp": entry.timestamp,
        }

    def _deserialize_entry(self, data: dict, url: str) -> MediaCacheEntry:
        """Reconstruct MediaCacheEntry from stored dict."""
        return MediaCacheEntry(
            url=data.get("url", url),
            content=data.get("content", b""),
            content_type=data.get("content_type", ""),
            extension=data.get("extension", ""),
            size_bytes=data.get("size_bytes", 0),
            timestamp=data.get("timestamp"),
        )
