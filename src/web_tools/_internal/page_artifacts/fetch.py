"""Fetch and cache raw page artifacts (HTML, MHTML, screenshots).

Internal module (not part of the stable public API).

This exists to share the cache-aware crawl step across multiple services
(html_reader, quote_manager, etc.) without creating cross-service imports.
"""

from __future__ import annotations

from py_lib_runtime import (
    CacheConfig,
    CacheEvents,
    cached,
    get_logger,
    log_operation_duration,
)

from web_tools._internal.page_artifacts.cache import (
    artifacts_to_cache_entry,
    cache_entry_to_artifacts,
    get_page_artifacts_cache,
    log_cache_hit,
    log_cache_miss,
    log_cache_store,
)
from web_tools._internal.page_artifacts.crawl import crawl_url
from web_tools._internal.page_artifacts.types import PageArtifacts

logger = get_logger(__name__)


@cached(
    get_page_artifacts_cache,
    options=CacheConfig(
        key_arg="url",
        force_refresh_arg="force_refresh",
        no_cache_arg="no_cache",
        to_entry=artifacts_to_cache_entry,
        from_entry=cache_entry_to_artifacts,
    ),
    events=CacheEvents(
        on_hit=log_cache_hit,
        on_miss=log_cache_miss,
        on_store=log_cache_store,
    ),
)
@log_operation_duration(logger, event_type="web_tools.fetch.completed")
async def fetch_html(
    url: str,
    *,
    force_refresh: bool = False,
    no_cache: bool = False,
    timeout_sec: float | None = None,
) -> PageArtifacts:
    """Fetch a URL and capture MHTML/screenshots, using the cache when enabled."""
    _ = force_refresh, no_cache
    return await crawl_url(url, timeout_sec=timeout_sec, capture_cache=True)
