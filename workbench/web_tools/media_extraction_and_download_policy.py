# %%
"""Workbench scenario: media extraction and download policy.

Why:
    Isolates real media URL extraction, policy gating, download bytes, and cache
    evidence without importing shipped `web_tools` code.

Covers:
    Area: media extraction and download policy
    Behavior: live page media extraction, disabled policy, allowed download, cache hit
    Interface: `httpx`, `lxml.html`, and `diskcache.Cache`

Checks:
    If a live page contains image URLs, then the probe extracts absolute media
    candidates from the real HTML.
    If media downloading is disabled, then candidates remain visible but no
    media bytes are downloaded.
    If image downloading is enabled, then the first live image returns content
    type, extension, byte size, and cache evidence on repeat use.
    If the total-download policy is zero, then the result is skipped before a
    media request is made.

Examples:
    Run manually:
        uv run python -m workbench.web_tools.media_extraction_and_download_policy
        uv run py-lib-reproduce-running-loop \
            workbench.web_tools.media_extraction_and_download_policy
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from urllib.parse import urljoin, urlparse

import httpx
from diskcache import Cache
from lxml import html
from py_lib_tooling import console

# =============================================================================
# Scenario
# =============================================================================

TEST_PAGE_URL = "https://www.python.org/"
_HTTP_TIMEOUT_SECONDS = 15
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class MediaType(StrEnum):
    """Stable media type vocabulary for this isolated probe."""

    IMAGE = "image"


@dataclass(frozen=True, slots=True)
class MediaConfig:
    """Validated media policy snapshot for this isolated probe."""

    enabled: bool = True
    allowed_types: tuple[MediaType, ...] = (MediaType.IMAGE,)
    max_total_downloads: int = 10
    cache_media: bool = True


@dataclass(frozen=True, slots=True)
class MediaItem:
    """Caller-visible downloaded media item for this isolated probe."""

    url: str
    content: bytes
    content_type: str
    extension: str
    size_bytes: int
    from_cache: bool


@dataclass(slots=True)
class DownloadStats:
    """Public workflow observability for this isolated probe."""

    downloads: int = 0
    direct_downloads: int = 0
    cache_hits: int = 0
    skipped_limit: int = 0


# =============================================================================
# Helpers
# =============================================================================


def fetch_live_page(url: str) -> tuple[str, str]:
    """Fetch a live HTML page and return text plus final URL."""
    response = httpx.get(url, follow_redirects=True, timeout=_HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.text, str(response.url)


def extract_image_urls(page_html: str, *, base_url: str) -> list[str]:
    """Extract absolute image URLs from real page HTML."""
    tree = html.fromstring(page_html)
    candidates: list[str] = []
    seen: set[str] = set()
    for raw_url in tree.xpath(
        "//img[@src]/@src | //meta[@property='og:image']/@content"
    ):
        url = urljoin(base_url, str(raw_url))
        if url in seen:
            continue
        if _classify_media_type(url) is None:
            continue
        candidates.append(url)
        seen.add(url)
    return candidates


def _cache_key(url: str) -> str:
    """Return a stable media cache key without exposing storage layout."""
    digest = hashlib.sha256(url.encode(), usedforsecurity=False).hexdigest()
    return f"media:{digest}"


def _extension_from_url(url: str) -> str:
    """Return a lowercase extension from a media URL path."""
    return Path(urlparse(url).path).suffix.lower()


def _classify_media_type(url: str) -> MediaType | None:
    """Classify media using public vocabulary."""
    if _extension_from_url(url) in {".png", ".jpg", ".jpeg", ".webp"}:
        return MediaType.IMAGE
    return None


def _is_allowed_media(url: str, config: MediaConfig) -> bool:
    """Return whether a URL is allowed by the media type policy."""
    media_type = _classify_media_type(url)
    return media_type in config.allowed_types


def _content_type_from_response(response: httpx.Response, *, extension: str) -> str:
    """Return a response content type with a simple extension fallback."""
    content_type = response.headers.get("content-type", "").split(";", maxsplit=1)[0]
    if content_type:
        return content_type
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(extension, "application/octet-stream")


def _serialize_item(item: MediaItem | None) -> dict[str, object] | None:
    """Serialize public media item evidence."""
    if item is None:
        return None

    return {
        "url": item.url,
        "content_type": item.content_type,
        "extension": item.extension,
        "size_bytes": item.size_bytes,
        "from_cache": item.from_cache,
        "content_is_png": item.content.startswith(_PNG_SIGNATURE),
    }


# =============================================================================
# Pipeline
# =============================================================================


def download_media(
    url: str,
    *,
    config: MediaConfig,
    cache: Cache,
    stats: DownloadStats,
) -> MediaItem | None:
    """Download one real media URL if policy allows it."""
    if not config.enabled:
        return None

    if stats.downloads >= config.max_total_downloads:
        stats.skipped_limit += 1
        return None

    if not _is_allowed_media(url, config):
        return None

    cache_key = _cache_key(url)
    if config.cache_media:
        cached_entry = cache.get(cache_key)
        if isinstance(cached_entry, dict):
            cached = cast("dict[str, object]", cached_entry)
            content = cached["content"]
            if not isinstance(content, bytes):
                msg = "Cached media content must be bytes."
                raise TypeError(msg)
            stats.cache_hits += 1
            return MediaItem(
                url=str(cached["url"]),
                content=content,
                content_type=str(cached["content_type"]),
                extension=str(cached["extension"]),
                size_bytes=int(cached["size_bytes"]),
                from_cache=True,
            )

    response = httpx.get(url, follow_redirects=True, timeout=_HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    extension = _extension_from_url(str(response.url))
    item = MediaItem(
        url=str(response.url),
        content=response.content,
        content_type=_content_type_from_response(response, extension=extension),
        extension=extension,
        size_bytes=len(response.content),
        from_cache=False,
    )
    stats.downloads += 1
    stats.direct_downloads += 1

    if config.cache_media:
        cache[cache_key] = {
            "url": item.url,
            "content": item.content,
            "content_type": item.content_type,
            "extension": item.extension,
            "size_bytes": item.size_bytes,
        }

    return item


def run_disabled_policy(*, candidates: list[str]) -> dict[str, object]:
    """Run disabled media policy over real extracted candidates."""
    config = MediaConfig(enabled=False)
    return {
        "candidate_count": len(candidates),
        "enabled": config.enabled,
        "post_download_count": 0,
    }


def run_enabled_policy(*, media_url: str, cache_dir: Path) -> dict[str, object]:
    """Run allowed live image download and cache-hit behavior."""
    stats = DownloadStats()
    with Cache(str(cache_dir)) as cache:
        first_item = download_media(
            media_url,
            config=MediaConfig(),
            cache=cache,
            stats=stats,
        )
        cached_item = download_media(
            media_url,
            config=MediaConfig(),
            cache=cache,
            stats=stats,
        )

    return {
        "first_item": _serialize_item(first_item),
        "cached_item": _serialize_item(cached_item),
        "stats": {
            "downloads": stats.downloads,
            "direct_downloads": stats.direct_downloads,
            "cache_hits": stats.cache_hits,
            "skipped_limit": stats.skipped_limit,
        },
    }


def run_limit_policy(*, media_url: str, cache_dir: Path) -> dict[str, object]:
    """Run total-limit skip behavior before any media request is made."""
    stats = DownloadStats()
    with Cache(str(cache_dir)) as cache:
        item = download_media(
            media_url,
            config=MediaConfig(max_total_downloads=0),
            cache=cache,
            stats=stats,
        )

    return {
        "item": _serialize_item(item),
        "downloads": stats.downloads,
        "skipped_limit": stats.skipped_limit,
    }


def run_pipeline(*, page_url: str, cache_root: Path) -> dict[str, object]:
    """Run the isolated live media extraction and policy flow."""
    page_html, final_url = fetch_live_page(page_url)
    candidates = extract_image_urls(page_html, base_url=final_url)
    if not candidates:
        msg = f"No image candidates found on live page: {final_url}."
        raise RuntimeError(msg)

    first_url = candidates[0]
    return {
        "page": {
            "url": final_url,
            "candidate_count": len(candidates),
            "first_candidate": first_url,
        },
        "disabled": run_disabled_policy(candidates=candidates),
        "enabled": run_enabled_policy(
            media_url=first_url,
            cache_dir=cache_root / "media_cache",
        ),
        "limited": run_limit_policy(
            media_url=first_url,
            cache_dir=cache_root / "limited_media_cache",
        ),
    }


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the workbench script as a narrative manual demo."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Fetching a live page, extracting real image URLs, then applying "
        "isolated media policy and cache behavior.",
        details=(f"page_url: {TEST_PAGE_URL}",),
    )

    with TemporaryDirectory() as temp_dir:
        evidence = run_pipeline(page_url=TEST_PAGE_URL, cache_root=Path(temp_dir))

    console.demo_step(
        "Observed Media Policy",
        "The isolated flow exposed real extraction, a real image download, "
        "cache evidence, disabled policy, and a limit skip.",
    )
    console.print_json(evidence)
    console.demo_outcome(
        "The media workflow is now backed by live HTTP, real HTML, real media "
        "bytes, and a real cache dependency.",
    )


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
{
  "disabled": {
    "candidate_count": 2,
    "enabled": false,
    "post_download_count": 0
  },
  "enabled": {
    "cached_item": {
      "content_is_png": true,
      "content_type": "image/png",
      "extension": ".png",
      "from_cache": true,
      "size_bytes": 7821
    },
    "first_item": {
      "content_is_png": true,
      "content_type": "image/png",
      "extension": ".png",
      "from_cache": false,
      "size_bytes": 7821
    },
    "stats": {
      "cache_hits": 1,
      "direct_downloads": 1,
      "downloads": 1,
      "skipped_limit": 0
    }
  },
  "limited": {
    "downloads": 0,
    "item": null,
    "skipped_limit": 1
  },
  "page": {
    "candidate_count": 2,
    "first_candidate": "https://www.python.org/static/opengraph-icon-200x200.png",
    "url": "https://www.python.org/"
  }
}
""".strip()
