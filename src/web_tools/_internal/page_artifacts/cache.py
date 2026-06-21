"""Cache glue for page artifacts.

Internal module (not part of the stable public API).
"""

from __future__ import annotations

from typing import Any

from py_lib_runtime import get_logger

from web_tools._internal.cache.manager import (
    CacheEntry,
    CacheManager,
    get_cache,
)
from web_tools._internal.page_artifacts.types import PageArtifacts

logger = get_logger(__name__)


def get_page_artifacts_cache(_: dict[str, Any]) -> CacheManager | None:
    """Return the configured web_tools HTML cache, if enabled."""
    return get_cache()


def artifacts_to_cache_entry(result: PageArtifacts, _: dict[str, Any]) -> CacheEntry:
    """Convert fetched artifacts to a cache entry."""
    return CacheEntry(
        url=result.url,
        html=result.html,
        mhtml=result.mhtml,
        screenshot=result.screenshot,
    )


def cache_entry_to_artifacts(entry: CacheEntry) -> PageArtifacts:
    """Convert a cache entry back into fetched artifacts."""
    return PageArtifacts(
        html=entry.html,
        url=entry.url,
        mhtml=entry.mhtml,
        screenshot=entry.screenshot,
    )


def log_cache_hit(bound: dict[str, Any]) -> None:
    """Log a cache hit."""
    url = bound["url"]
    logger.info(
        "Page artifact cache hit",
        event_type="web_tools.cache.hit",
        url=url,
    )


def log_cache_miss(bound: dict[str, Any]) -> None:
    """Log a cache miss."""
    url = bound["url"]
    logger.info(
        "Page artifact cache miss",
        event_type="web_tools.cache.miss",
        url=url,
    )


def log_cache_store(bound: dict[str, Any]) -> None:
    """Log a cache store."""
    url = bound["url"]
    logger.info(
        "Page artifact cached",
        event_type="web_tools.cache.stored",
        url=url,
    )
