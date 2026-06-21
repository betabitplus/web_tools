"""Media extraction public-contract properties.

Why:
    Protects generated invariants for public media config and disabled media
    extraction without performing downloads.

Covers:
    Area: media extraction and download policy
    Behavior: config normalization, URL extraction, disabled download policy
    Interface: `MediaConfig`, `MediaDownloader`, and `MediaType`

Checks:
    If callers provide supported media type values, then `MediaConfig`
    normalizes them into an immutable public snapshot.
    If generated post-like payloads are inspected with downloads disabled, then
    media URLs remain extractable and downloads remain empty.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from web_tools import (
    InvalidConfigValueError,
    MediaConfig,
    MediaDownloader,
    MediaType,
    WebToolsError,
)

# =============================================================================
# Strategies
# =============================================================================

_PROPERTY_SETTINGS = settings(max_examples=40)

_SUPPORTED_MEDIA_TYPE_VALUES = tuple(media_type.value for media_type in MediaType)
_MEDIA_TYPE_INPUT = st.one_of(
    st.sampled_from(tuple(MediaType)),
    st.sampled_from(_SUPPORTED_MEDIA_TYPE_VALUES),
)
_MEDIA_TYPE_SEQUENCE = st.lists(_MEDIA_TYPE_INPUT, min_size=1, max_size=6)

_UNKNOWN_MEDIA_TYPE = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=12,
).filter(lambda value: value not in _SUPPORTED_MEDIA_TYPE_VALUES)

_SLUG = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=12,
)
_BOOLEAN = st.booleans()


# =============================================================================
# Helpers
# =============================================================================


def normalize_media_type_input(value: MediaType | str) -> str:
    """Return the public media type name for generated config input."""
    if isinstance(value, MediaType):
        return value.value
    return value


def build_media_post(*, slug: str) -> dict[str, object]:
    """Build a generated post-like payload with supported media locations."""
    image_url = f"https://i.redd.it/{slug}.jpg"
    preview_url = f"https://preview.redd.it/{slug}.png?width=640&amp;token=ok"
    video_url = f"https://v.redd.it/{slug}/DASH_720.mp4"
    thumbnail_url = f"https://i.redd.it/{slug}-thumb.jpg"
    return {
        "url": image_url,
        "preview": {"images": [{"source": {"url": preview_url}}]},
        "media": {"reddit_video": {"fallback_url": video_url}},
        "thumbnail": thumbnail_url,
    }


# =============================================================================
# Assertions
# =============================================================================


def assert_media_config_snapshot(
    config: MediaConfig,
    *,
    allowed_types: list[MediaType | str],
) -> None:
    """Assert generated media config normalization."""
    # Public config construction should coerce enum/string inputs once and then
    # expose a stable immutable tuple snapshot.
    assert isinstance(config.allowed_types, tuple)
    assert config.allowed_types == tuple(
        normalize_media_type_input(value) for value in allowed_types
    )


def assert_disabled_downloader_behavior(
    *,
    urls: list[str],
    items: list[object],
    stats: dict[str, object],
    download_thumbnails: bool,
) -> None:
    """Assert disabled policy extracts URLs but performs no downloads."""
    # Extraction should expose normalized URL candidates without HTML entities.
    assert urls
    assert all("&amp;" not in url for url in urls)
    assert len(urls) == len(set(urls))

    # Thumbnail extraction is controlled by public policy.
    assert any("thumb" in url for url in urls) is download_thumbnails

    # Disabled media policy should never return downloaded items.
    assert items == []
    assert stats["enabled"] is False
    assert stats["downloads"] == 0


# =============================================================================
# Properties
# =============================================================================


@_PROPERTY_SETTINGS
@given(allowed_types=_MEDIA_TYPE_SEQUENCE)
def test_media_config_normalizes_generated_public_media_types(
    allowed_types: list[MediaType | str],
) -> None:
    """Generated supported media type inputs should normalize at construction."""
    config = MediaConfig(allowed_types=allowed_types)

    assert_media_config_snapshot(config, allowed_types=allowed_types)


@_PROPERTY_SETTINGS
@given(unknown_media_type=_UNKNOWN_MEDIA_TYPE)
def test_media_config_rejects_generated_unknown_media_types(
    unknown_media_type: str,
) -> None:
    """Generated unsupported media type names should fail at the public edge."""
    with pytest.raises(InvalidConfigValueError) as exc_info:
        MediaConfig(allowed_types=[unknown_media_type])

    error = exc_info.value
    assert isinstance(error, WebToolsError)
    assert error.field == "allowed_types"
    assert unknown_media_type in str(error.value)


@_PROPERTY_SETTINGS
@given(slug=_SLUG, download_thumbnails=_BOOLEAN)
def test_disabled_media_downloader_extracts_without_downloads(
    *,
    slug: str,
    download_thumbnails: bool,
) -> None:
    """Generated post media candidates should remain safe when downloads are off."""
    config = MediaConfig(
        enabled=False,
        download_thumbnails=download_thumbnails,
    )
    post_data = build_media_post(slug=slug)

    with MediaDownloader(config=config, cache_dir=None) as downloader:
        urls = downloader.extract_media_urls(post_data)
        items = downloader.download_from_post(post_data)
        stats = downloader.stats()

    assert_disabled_downloader_behavior(
        urls=urls,
        items=items,
        stats=stats,
        download_thumbnails=download_thumbnails,
    )
