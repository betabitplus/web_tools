"""Public media download facade.

Why:
    Makes the supported media downloader constructor and methods explicit while
    HTTP routing, cache management, and download mechanics stay private.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from web_tools._api.config import MediaConfig
from web_tools._api.types import MediaItem
from web_tools._internal import MediaDownloaderRuntime

# ================================================================================
# Public API
# ================================================================================


class MediaDownloader:
    """Public facade for downloading media from URL and post payload inputs."""

    def __init__(
        self,
        config: MediaConfig | None = None,
        cache_dir: str | Path | None = None,
        http_client: httpx.Client | None = None,
        proxy: str | None = None,
    ) -> None:
        """Create a media downloader with optional config and transport overrides."""
        self._runtime = MediaDownloaderRuntime(
            config=config,
            cache_dir=cache_dir,
            http_client=http_client,
            proxy=proxy,
        )

    def __enter__(self) -> MediaDownloader:
        """Enter the downloader context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Close downloader resources when leaving a context manager."""
        _ = exc_type, exc, traceback
        self.close()

    @property
    def config(self) -> MediaConfig:
        """Return the validated media download config snapshot."""
        return self._runtime.config

    def download(self, url: str) -> MediaItem | None:
        """Download one media URL when config and limits allow it."""
        return self._runtime.download(url)

    def extract_media_urls(self, post_data: dict[str, Any]) -> list[str]:
        """Extract candidate media URLs from one post-like payload."""
        return self._runtime.extract_media_urls(post_data)

    def download_from_post(self, post_data: dict[str, Any]) -> list[MediaItem]:
        """Download eligible media URLs from one post-like payload."""
        return self._runtime.download_from_post(post_data)

    def stats(self) -> dict[str, Any]:
        """Return media download counters for observability."""
        return self._runtime.stats()

    def close(self) -> None:
        """Close internally owned cache and HTTP resources."""
        self._runtime.close()
