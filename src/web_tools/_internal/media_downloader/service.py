"""media_downloader service orchestrator.

Internal module (not part of the stable public API).
The stable entrypoint is `web_tools`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from py_lib_runtime import get_logger, log_operation_duration, resolve_cache_dir

from web_tools._api.errors import MediaDownloadError
from web_tools._api.types import MediaItem
from web_tools._internal.config import MediaConfig, get_default_web_tools_resolver
from web_tools._internal.media_downloader.media_cache import (
    get_cached_media,
    init_media_cache,
    save_media_to_cache,
)
from web_tools._internal.media_downloader.media_http import (
    create_direct_client,
    create_proxy_client,
    estimate_size_mb,
    streaming_download,
)
from web_tools._internal.media_downloader.media_routing import (
    extract_media_urls,
    get_extension_from_url,
    is_allowed_type,
    should_use_proxy,
)

logger = get_logger(__name__)


class MediaDownloader:  # pylint: disable=too-many-instance-attributes
    """Downloads and caches media from Reddit posts."""

    def __init__(
        self,
        config: MediaConfig | None = None,
        cache_dir: str | Path | None = None,
        http_client: httpx.Client | None = None,
        proxy: str | None = None,
    ) -> None:
        """Initialize the downloader with optional overrides."""
        defaults = get_default_web_tools_resolver().defaults

        self.config = config or defaults.media_download
        self._cache_dir = resolve_cache_dir(cache_dir, namespace="web_tools/media")
        self._proxy = proxy
        self._external_client = http_client is not None
        self._proxy_client = http_client
        self._direct_client: httpx.Client | None = None

        self._media_cache_max_size_bytes = defaults.media_cache_max_size_bytes
        self._proxy_timeout_seconds = defaults.media_proxy_timeout_seconds
        self._direct_timeout_seconds = defaults.media_direct_timeout_seconds

        self._cache = init_media_cache(
            enabled=self.config.enabled,
            cache_media=self.config.cache_media,
            cache_dir=self._cache_dir,
            max_size_bytes=self._media_cache_max_size_bytes,
        )

        self._download_count = 0
        self._cache_hits = 0
        self._skipped_size = 0
        self._skipped_type = 0
        self._proxy_downloads = 0
        self._direct_downloads = 0
        self._proxy_aborts = 0

    def __enter__(self) -> MediaDownloader:
        """Context-manager entry; returns `self`."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Context-manager exit; closes internal resources."""
        _ = (exc_type, exc, traceback)
        self.close()

    def _get_proxy_client(self) -> httpx.Client:
        """Return a lazily-created proxy client (or the injected client)."""
        if self._proxy_client is None:
            self._proxy_client = create_proxy_client(
                timeout_seconds=self._proxy_timeout_seconds,
                proxy=self._proxy,
            )
        return self._proxy_client

    def _get_direct_client(self) -> httpx.Client:
        """Return a lazily-created direct client."""
        if self._direct_client is None:
            self._direct_client = create_direct_client(
                timeout_seconds=self._direct_timeout_seconds,
            )
        return self._direct_client

    def _should_use_proxy(
        self,
        url: str,
        estimated_size_mb: float | None = None,
    ) -> bool:
        """Compatibility shim for existing tests/internal callers."""
        return should_use_proxy(
            url,
            estimated_size_mb=estimated_size_mb,
            config=self.config,
        )

    def _estimate_size_mb(self, url: str) -> float | None:
        """Estimate file size in MB via HEAD, when enabled."""
        if self.config.skip_head:
            return None

        head_client = (
            self._get_proxy_client()
            if self.config.use_proxy_for_small
            else self._get_direct_client()
        )
        return estimate_size_mb(url, head_client=head_client)

    def _skip_if_disallowed_type(self, url: str) -> bool:
        """Return true if the URL should be skipped due to disallowed type."""
        # Some valid media URLs (e.g., CDNs) omit file extensions.
        # In that case we can't infer type up-front; defer the check to the
        # response Content-Type validation.
        if not get_extension_from_url(url):
            return False

        if is_allowed_type(url, content_type="", config=self.config):
            return False

        self._skipped_type += 1
        logger.debug(
            "Skipping media (type not allowed)",
            event_type="web_tools.media.skip.type",
            url=url,
        )
        return True

    def _client_for_route(self, *, use_proxy: bool) -> tuple[httpx.Client, str]:
        """Choose the HTTP client for a route and return (client, label)."""
        if use_proxy:
            return self._get_proxy_client(), "proxy"
        return self._get_direct_client(), "direct"

    def _apply_skip_reason(self, reason: str) -> None:
        """Update skip counters based on a download result reason."""
        if reason == "skip_type":
            self._skipped_type += 1
        elif reason == "skip_size":
            self._skipped_size += 1

    def _download_result_to_item(
        self,
        url: str,
        *,
        use_proxy: bool,
        result_reason: str,
        result_item: MediaItem | None,
        result_error: Exception | None,
    ) -> tuple[MediaItem | None, bool]:
        """Convert a download result into (item, used_proxy) and update stats."""
        if result_reason in ("skip_type", "skip_size"):
            self._apply_skip_reason(result_reason)
            return None, use_proxy

        if result_reason == "error":
            raise MediaDownloadError(url=url, cause=result_error)

        if (
            result_reason == "abort_proxy"
            and use_proxy
            and not self.config.use_proxy_for_large
        ):
            logger.info(
                "Retrying with direct connection",
                event_type="web_tools.media.retry.direct",
                url=url,
            )
            direct_result = streaming_download(
                url,
                client=self._get_direct_client(),
                config=self.config,
                use_proxy=False,
            )
            if direct_result.item is not None:
                self._proxy_aborts += 1
                return direct_result.item, False

            if direct_result.reason == "error":
                raise MediaDownloadError(url=url, cause=direct_result.error)

            self._apply_skip_reason(direct_result.reason)
            return None, False

        return result_item, use_proxy

    def _download_live(self, url: str) -> tuple[MediaItem | None, bool]:
        """Download without checking the cache; returns (item, used_proxy)."""
        if self._skip_if_disallowed_type(url):
            return None, False

        estimated = self._estimate_size_mb(url)
        use_proxy = should_use_proxy(
            url,
            estimated_size_mb=estimated,
            config=self.config,
        )
        client, client_type = self._client_for_route(use_proxy=use_proxy)
        logger.debug(
            "Selected media download connection",
            event_type="web_tools.media.connection.selected",
            client_type=client_type,
            url=url,
            estimated_size_mb=estimated,
        )

        result = streaming_download(
            url,
            client=client,
            config=self.config,
            use_proxy=use_proxy,
        )
        return self._download_result_to_item(
            url,
            use_proxy=use_proxy,
            result_reason=result.reason,
            result_item=result.item,
            result_error=result.error,
        )

    @log_operation_duration(logger, event_type="web_tools.media.download.completed")
    def download(self, url: str) -> MediaItem | None:
        """Download a single media URL, respecting limits and caching."""
        if not self.config.enabled:
            return None

        if self._download_count >= self.config.max_total_downloads:
            logger.debug(
                "Max total downloads reached",
                event_type="web_tools.media.limit.total",
                max_total_downloads=self.config.max_total_downloads,
            )
            return None

        cached = get_cached_media(self._cache, url)
        if cached:
            self._cache_hits += 1
            logger.debug(
                "Cache hit for media",
                event_type="web_tools.media.cache.hit",
                url=url,
            )
            return cached

        item, used_proxy = self._download_live(url)
        if item is None:
            return None

        item.timestamp = datetime.now(UTC).isoformat()
        self._download_count += 1
        if used_proxy:
            self._proxy_downloads += 1
        else:
            self._direct_downloads += 1
        if self.config.cache_media:
            save_media_to_cache(self._cache, item)
        return item

    def extract_media_urls(self, post_data: dict[str, Any]) -> list[str]:
        """Extract candidate media URLs from a Reddit post payload."""
        return extract_media_urls(
            post_data,
            download_thumbnails=self.config.download_thumbnails,
        )

    @log_operation_duration(
        logger, event_type="web_tools.media.download_from_post.completed"
    )
    def download_from_post(self, post_data: dict[str, Any]) -> list[MediaItem]:
        """Download all eligible media for a Reddit post payload."""
        if not self.config.enabled:
            return []

        urls = self.extract_media_urls(post_data)
        if not urls:
            return []

        urls = urls[: self.config.max_downloads_per_post]

        items: list[MediaItem] = []
        for url in urls:
            if self._download_count >= self.config.max_total_downloads:
                logger.debug(
                    "Max total downloads reached",
                    event_type="web_tools.media.limit.total",
                    max_total_downloads=self.config.max_total_downloads,
                )
                break

            item = self.download(url)
            if item:
                items.append(item)

        return items

    def stats(self) -> dict[str, Any]:
        """Return counters for observability and debugging."""
        return {
            "enabled": self.config.enabled,
            "downloads": self._download_count,
            "proxy_downloads": self._proxy_downloads,
            "direct_downloads": self._direct_downloads,
            "proxy_aborts": self._proxy_aborts,
            "cache_hits": self._cache_hits,
            "skipped_size": self._skipped_size,
            "skipped_type": self._skipped_type,
            "max_total": self.config.max_total_downloads,
            "remaining": max(0, self.config.max_total_downloads - self._download_count),
            "proxy_threshold_mb": self.config.proxy_size_threshold_mb,
        }

    def close(self) -> None:
        """Close any internally owned cache/HTTP clients."""
        if self._cache:
            self._cache.close()
        if self._proxy_client and not self._external_client:
            self._proxy_client.close()
        if self._direct_client:
            self._direct_client.close()
