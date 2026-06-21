"""Public output and error contract properties.

Why:
    Protects generated invariants for public DTOs, manifests, response counts,
    vocabulary values, and public error attribution.

Covers:
    Area: public output and errors
    Behavior: manifest counts, serialized element output, response counts, errors
    Interface: public DTOs, vocabulary, and `WebToolsError` subclasses

Checks:
    If callers receive generated manifest elements, then counts and serialized
    element data remain in public vocabulary.
    If media download responses contain generated items, then `count` reflects
    the public item list length.
    If public errors are constructed with generated attribution, then that
    attribution remains visible through public fields.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

from web_tools import (
    MediaDownloadError,
    MediaDownloadResponse,
    MediaItem,
    VisualElement,
    VisualElementManifest,
    VisualElementType,
    WebToolsError,
)

# =============================================================================
# Strategies
# =============================================================================

_PROPERTY_SETTINGS = settings(max_examples=40)

_COUNT = st.integers(min_value=0, max_value=5)
_SAFE_TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_./:",
    min_size=1,
    max_size=40,
)
_CONTENT = st.binary(min_size=0, max_size=24)


# =============================================================================
# Helpers
# =============================================================================


def build_manifest(
    *, picture_count: int, table_count: int, math_count: int
) -> VisualElementManifest:
    """Build a public manifest with generated category counts."""
    elements = [
        VisualElement(
            id=f"P_{index}",
            element_type=VisualElementType.PICTURE,
            index=index,
            src=f"https://example.com/{index}.png",
            alt=f"Picture {index}",
        )
        for index in range(picture_count)
    ]
    elements.extend(
        VisualElement(
            id=f"T_{index}",
            element_type=VisualElementType.TABLE,
            index=index,
            row_count=index + 1,
        )
        for index in range(table_count)
    )
    elements.extend(
        VisualElement(
            id=f"M_{index}",
            element_type=VisualElementType.MATH,
            index=index,
            latex=f"x_{index}",
        )
        for index in range(math_count)
    )
    return VisualElementManifest(elements=elements)


def build_media_items(*, count: int, content: bytes, url_stem: str) -> list[MediaItem]:
    """Build generated public media items."""
    return [
        MediaItem(
            url=f"https://example.com/{url_stem}-{index}.png",
            content=content,
            content_type="image/png",
            extension=".png",
            size_bytes=len(content),
            from_cache=index % 2 == 0,
        )
        for index in range(count)
    ]


# =============================================================================
# Assertions
# =============================================================================


def assert_manifest_public_contract(
    manifest: VisualElementManifest,
    *,
    picture_count: int,
    table_count: int,
    math_count: int,
) -> None:
    """Assert generated manifest count and lookup behavior."""
    expected_counts = {
        "total": picture_count + table_count + math_count,
        "picture": picture_count,
        "table": table_count,
        "math": math_count,
    }
    assert manifest.counts == expected_counts

    serialized = manifest.to_dict()
    assert serialized["counts"] == {
        "picture": picture_count,
        "table": table_count,
        "math": math_count,
    }
    assert len(serialized["elements"]) == expected_counts["total"]

    # Existing IDs should look up the same public element object; missing IDs
    # should stay a clean `None`.
    for element in manifest.elements:
        assert manifest.get_element(element.id) is element
    assert manifest.get_element("P_999999") is None


def assert_media_download_response_contract(
    response: MediaDownloadResponse,
    *,
    expected_count: int,
) -> None:
    """Assert generated media response count behavior."""
    assert response.count == expected_count
    assert len(response.items) == expected_count


def assert_public_media_error(
    error: MediaDownloadError, *, url: str, reason: str
) -> None:
    """Assert public media error attribution."""
    assert isinstance(error, WebToolsError)
    assert error.url == url
    assert error.reason == reason
    assert reason in str(error)


# =============================================================================
# Properties
# =============================================================================


@_PROPERTY_SETTINGS
@given(
    picture_count=_COUNT,
    table_count=_COUNT,
    math_count=_COUNT,
)
def test_visual_manifest_counts_generated_public_elements(
    *,
    picture_count: int,
    table_count: int,
    math_count: int,
) -> None:
    """Generated public visual elements should report stable manifest counts."""
    manifest = build_manifest(
        picture_count=picture_count,
        table_count=table_count,
        math_count=math_count,
    )

    assert_manifest_public_contract(
        manifest,
        picture_count=picture_count,
        table_count=table_count,
        math_count=math_count,
    )


@_PROPERTY_SETTINGS
@given(count=_COUNT, content=_CONTENT, url_stem=_SAFE_TEXT)
def test_media_download_response_count_matches_generated_items(
    *,
    count: int,
    content: bytes,
    url_stem: str,
) -> None:
    """Generated media download responses should count returned items."""
    items = build_media_items(count=count, content=content, url_stem=url_stem)
    response = MediaDownloadResponse(items=items, stats={"generated": True})

    assert_media_download_response_contract(response, expected_count=count)


@_PROPERTY_SETTINGS
@given(url=_SAFE_TEXT, reason=_SAFE_TEXT)
def test_media_download_error_preserves_generated_public_attribution(
    *,
    url: str,
    reason: str,
) -> None:
    """Generated media errors should keep public attribution fields."""
    error = MediaDownloadError(url=url, reason=reason)

    assert_public_media_error(error, url=url, reason=reason)
