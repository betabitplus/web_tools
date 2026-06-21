# %%
"""Media extraction and download policy e2e.

Why:
    Verifies that public media policy controls extraction, downloading,
    caching, skipped results, and transport errors without exposing downloader
    internals.

Covers:
    Area: media extraction and download policy
    Behavior: post URL extraction, policy-gated download, cache evidence, skips
    Interface: `MediaDownloader`, `MediaConfig`, `MediaType`, and `MediaItem`

Checks:
    If media downloading is disabled, then candidate URLs remain extractable
    but post downloads return an empty list.
    If image downloading is enabled for a loopback media URL, then the public
    downloader returns a `MediaItem` and exposes cache evidence on repeat use.
    If media policy blocks a type or total limit, then the public result is
    skipped without requiring caller knowledge of private routing.
    If media transport fails, then the public downloader raises
    `MediaDownloadError`.

Examples:
    Run manually:
        uv run python -m \
            tests.web_tools.e2e.media_extraction_and_download_policy.test_media_policy_pipeline

    Run as test:
        pytest \
            tests/web_tools/e2e/media_extraction_and_download_policy/test_media_policy_pipeline.py
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from typing import Any

import pytest
from py_lib_tooling import console

from web_tools import (
    MediaConfig,
    MediaDownloader,
    MediaDownloadError,
    MediaItem,
    MediaType,
    WebToolsError,
)

pytestmark = [
    pytest.mark.e2e_behavior,
    pytest.mark.e2e_contract,
    pytest.mark.hermetic,
]


# =============================================================================
# Scenario
# =============================================================================

TEST_MEDIA_BASE_URL = "http://127.0.0.1:0"
MEDIA_IMAGE_PATH = "/assets/media-image.png"
DISALLOWED_GIF_PATH = "/assets/media-animation.gif"
MISSING_IMAGE_PATH = "/assets/missing-media.png"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


# =============================================================================
# Helpers
# =============================================================================


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves media fixtures without request logs."""

    def log_message(self, format_string: str, *args: object) -> None:
        """Suppress per-request access logs during manual runs."""
        _ = format_string, args


@contextmanager
def serve_fixture_site() -> Iterator[str]:
    """Serve the committed e2e fixture site for manual execution."""
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "site"
    handler = partial(_QuietStaticHandler, directory=str(fixture_root))

    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/index.html"
        finally:
            server.shutdown()
            thread.join(timeout=5)


def media_url(site_url: str, path: str = MEDIA_IMAGE_PATH) -> str:
    """Build a loopback media URL from the shared e2e site URL."""
    site_root = site_url.rsplit("/", maxsplit=1)[0]
    return f"{site_root}{path}"


def build_post_data(*, image_url: str, gif_url: str) -> dict[str, Any]:
    """Build representative post-like media input."""
    return {
        "url": image_url,
        "preview": {
            "images": [
                {"source": {"url": f"{image_url}?preview=1&amp;token=ok"}},
            ],
        },
        "gallery_data": {
            "items": [
                {"media_id": "gallery_image"},
                {"media_id": "gallery_gif"},
            ],
        },
        "media_metadata": {
            "gallery_image": {"s": {"u": f"{image_url}?gallery=1&amp;token=ok"}},
            "gallery_gif": {"s": {"gif": gif_url}},
        },
        "thumbnail": f"{image_url}?thumbnail=1",
    }


def enabled_image_config(**overrides: object) -> MediaConfig:
    """Build media config for direct loopback image downloads."""
    values = {
        "enabled": True,
        "allowed_types": [MediaType.IMAGE],
        "max_downloads_per_post": 1,
        "max_total_downloads": 10,
        "cache_media": True,
        "download_thumbnails": False,
        "skip_head": True,
        "use_proxy_for_small": False,
        "use_proxy_for_large": False,
    }
    values.update(overrides)
    return MediaConfig(**values)


def serialize_item(item: MediaItem | None) -> dict[str, object] | None:
    """Serialize stable public media item evidence."""
    if item is None:
        return None

    return {
        "url": item.url,
        "content_type": item.content_type,
        "extension": item.extension,
        "size_bytes": item.size_bytes,
        "from_cache": item.from_cache,
        "content_is_png": item.content.startswith(_PNG_SIGNATURE),
        "has_timestamp": item.timestamp is not None,
    }


def serialize_error(error: MediaDownloadError) -> dict[str, object]:
    """Serialize public media error evidence."""
    return {
        "type": type(error).__name__,
        "is_web_tools_error": isinstance(error, WebToolsError),
        "url": error.url,
        "has_cause": error.cause is not None,
    }


# =============================================================================
# Pipeline
# =============================================================================


def run_disabled_policy(*, post_data: dict[str, Any]) -> dict[str, object]:
    """Run disabled media policy through the public facade."""
    with MediaDownloader(
        config=MediaConfig(enabled=False), cache_dir=None
    ) as downloader:
        urls = downloader.extract_media_urls(post_data)
        items = downloader.download_from_post(post_data)
        stats = downloader.stats()

    return {
        "extracted_count": len(urls),
        "post_download_count": len(items),
        "stats_enabled": stats["enabled"],
    }


def run_enabled_policy(
    *,
    image_url: str,
    gif_url: str,
    post_data: dict[str, Any],
    cache_dir: Path,
) -> dict[str, object]:
    """Run enabled image download, cache-hit, and skip behavior."""
    with MediaDownloader(
        config=enabled_image_config(),
        cache_dir=cache_dir,
    ) as downloader:
        urls = downloader.extract_media_urls(post_data)
        post_items = downloader.download_from_post(post_data)
        cached_item = downloader.download(image_url)
        disallowed_item = downloader.download(gif_url)
        stats = downloader.stats()

    return {
        "extracted_count": len(urls),
        "first_url": urls[0],
        "post_download_count": len(post_items),
        "post_items": [serialize_item(item) for item in post_items],
        "cached_item": serialize_item(cached_item),
        "disallowed_item": serialize_item(disallowed_item),
        "stats": {
            "downloads": stats["downloads"],
            "direct_downloads": stats["direct_downloads"],
            "cache_hits": stats["cache_hits"],
            "skipped_type": stats["skipped_type"],
        },
    }


def run_limit_policy(*, image_url: str, cache_dir: Path) -> dict[str, object]:
    """Run total-limit skip behavior through the public facade."""
    with MediaDownloader(
        config=enabled_image_config(max_total_downloads=0),
        cache_dir=cache_dir,
    ) as downloader:
        item = downloader.download(image_url)
        stats = downloader.stats()

    return {
        "item": serialize_item(item),
        "downloads": stats["downloads"],
        "remaining": stats["remaining"],
    }


def run_transport_error(*, missing_url: str, cache_dir: Path) -> dict[str, object]:
    """Run a failed media download and return public error evidence."""
    with MediaDownloader(
        config=enabled_image_config(cache_media=False),
        cache_dir=cache_dir,
    ) as downloader:
        try:
            downloader.download(missing_url)
        except MediaDownloadError as error:
            return serialize_error(error)

    msg = "Expected MediaDownloadError for missing media URL."
    raise AssertionError(msg)


# =============================================================================
# Assertions
# =============================================================================


def assert_disabled_policy(result: dict[str, object]) -> None:
    """Assert disabled media policy evidence."""
    # The public extractor still sees post media candidates.
    assert result["extracted_count"] == 4

    # Disabled policy prevents post downloads and exposes the disabled state.
    assert result["post_download_count"] == 0
    assert result["stats_enabled"] is False


def assert_enabled_policy(
    *,
    result: dict[str, object],
    image_url: str,
) -> None:
    """Assert enabled media policy, cache, and skip evidence."""
    # The post contains several candidates, but per-post policy allows one.
    assert result["extracted_count"] == 4
    assert result["first_url"] == image_url
    assert result["post_download_count"] == 1

    post_items = result["post_items"]
    assert isinstance(post_items, list)
    first_item = post_items[0]
    assert isinstance(first_item, dict)
    assert first_item["url"] == image_url
    assert first_item["content_type"] == "image/png"
    assert first_item["extension"] == ".png"
    assert first_item["content_is_png"] is True
    assert first_item["from_cache"] is False

    cached_item = result["cached_item"]
    assert isinstance(cached_item, dict)
    assert cached_item["from_cache"] is True

    # A disallowed GIF URL is skipped by public policy instead of downloaded.
    assert result["disallowed_item"] is None
    assert result["stats"] == {
        "downloads": 1,
        "direct_downloads": 1,
        "cache_hits": 1,
        "skipped_type": 1,
    }


def assert_limit_policy(result: dict[str, object]) -> None:
    """Assert total-limit skip evidence."""
    assert result["item"] is None
    assert result["downloads"] == 0
    assert result["remaining"] == 0


def assert_transport_error(result: dict[str, object], *, missing_url: str) -> None:
    """Assert public media error evidence."""
    assert result == {
        "type": "MediaDownloadError",
        "is_web_tools_error": True,
        "url": missing_url,
        "has_cause": True,
    }


# =============================================================================
# Tests
# =============================================================================


def test_media_policy_pipeline_hermetic(
    tmp_path: Path,
    e2e_site_url: str,
) -> None:
    """Verify media extraction, download, cache, and skip policy."""
    image_url = media_url(e2e_site_url)
    gif_url = media_url(e2e_site_url, DISALLOWED_GIF_PATH)
    post_data = build_post_data(image_url=image_url, gif_url=gif_url)

    disabled = run_disabled_policy(post_data=post_data)
    enabled = run_enabled_policy(
        image_url=image_url,
        gif_url=gif_url,
        post_data=post_data,
        cache_dir=tmp_path / "media_cache",
    )
    limited = run_limit_policy(
        image_url=image_url,
        cache_dir=tmp_path / "limited_media_cache",
    )

    assert_disabled_policy(disabled)
    assert_enabled_policy(result=enabled, image_url=image_url)
    assert_limit_policy(limited)


def test_media_transport_errors_are_public(
    tmp_path: Path,
    e2e_site_url: str,
) -> None:
    """Verify failed media transport crosses as a public error."""
    missing_url = media_url(e2e_site_url, MISSING_IMAGE_PATH)
    result = run_transport_error(
        missing_url=missing_url,
        cache_dir=tmp_path / "error_media_cache",
    )

    assert_transport_error(result, missing_url=missing_url)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the e2e scenario as a direct live manual check."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Serving committed media fixtures over loopback and exercising policy.",
        details=(f"fixture_base_url: {TEST_MEDIA_BASE_URL}",),
    )

    with TemporaryDirectory() as temp_dir, serve_fixture_site() as site_url:
        image_url = media_url(site_url)
        gif_url = media_url(site_url, DISALLOWED_GIF_PATH)
        missing_url = media_url(site_url, MISSING_IMAGE_PATH)
        post_data = build_post_data(image_url=image_url, gif_url=gif_url)
        cache_root = Path(temp_dir)

        disabled = run_disabled_policy(post_data=post_data)
        enabled = run_enabled_policy(
            image_url=image_url,
            gif_url=gif_url,
            post_data=post_data,
            cache_dir=cache_root / "media_cache",
        )
        limited = run_limit_policy(
            image_url=image_url,
            cache_dir=cache_root / "limited_media_cache",
        )
        error = run_transport_error(
            missing_url=missing_url,
            cache_dir=cache_root / "error_media_cache",
        )

    assert_disabled_policy(disabled)
    assert_enabled_policy(result=enabled, image_url=image_url)
    assert_limit_policy(limited)
    assert_transport_error(error, missing_url=missing_url)

    console.demo_step(
        "Observed Media Policy",
        "The public downloader exposed extraction, one allowed download, cache "
        "evidence, skipped policy outcomes, and a public error.",
    )
    console.print_json(
        {
            "disabled": disabled,
            "enabled": enabled,
            "limited": limited,
            "error": error,
        }
    )
    console.demo_outcome(
        "This proves media work stays controlled by public policy and public "
        "result/error types.",
    )


if __name__ == "__main__":
    main()

# %%
