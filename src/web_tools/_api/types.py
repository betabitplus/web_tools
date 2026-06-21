"""Public vocabulary and DTO types for `web_tools`.

Why:
    Keeps stable caller-facing names and response shapes in one declaration
    module instead of scattering public DTOs through implementation code.

How:
    These values are portable public vocabulary and data contracts. Private
    code may populate them, but callers should not need to know those
    implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from PIL import Image

# ================================================================================
# Public Vocabulary
# ================================================================================


class MediaType(StrEnum):
    """Supported media download type names."""

    IMAGE = "image"
    GIF = "gif"
    VIDEO = "video"
    ALL = "all"


class VisualElementType(StrEnum):
    """Supported visual element categories emitted by HTML conversion."""

    PICTURE = "picture"
    TABLE = "table"
    MATH = "math"


# ================================================================================
# Visual Element Contracts
# ================================================================================


@dataclass(slots=True)
class VisualElement:
    """Metadata for a visual element in a converted document."""

    id: str
    element_type: VisualElementType
    index: int
    src: str | None = None
    alt: str | None = None
    row_count: int | None = None
    latex: str | None = None


class _VisualElementSerialization:
    """Serialize visual element DTOs for public metadata output."""

    @staticmethod
    def to_dict(element: VisualElement) -> dict[str, object]:
        """Convert one visual element to a JSON-serializable mapping."""
        data: dict[str, object] = {
            "id": element.id,
            "type": element.element_type.value,
            "index": element.index,
        }
        data.update(
            {
                key: value
                for key, value in (
                    ("src", element.src),
                    ("alt", element.alt),
                    ("row_count", element.row_count),
                    ("latex", element.latex),
                )
                if value is not None
            }
        )
        return data


@dataclass(slots=True)
class VisualElementManifest:
    """Collection of visual elements detected in a document."""

    elements: list[VisualElement] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        """Return counts for each supported visual element type."""
        return {
            "total": len(self.elements),
            "picture": sum(
                1
                for element in self.elements
                if element.element_type == VisualElementType.PICTURE
            ),
            "table": sum(
                1
                for element in self.elements
                if element.element_type == VisualElementType.TABLE
            ),
            "math": sum(
                1
                for element in self.elements
                if element.element_type == VisualElementType.MATH
            ),
        }

    def to_dict(self) -> dict[str, object]:
        """Convert the manifest to a JSON-serializable mapping."""
        counts = self.counts
        return {
            "elements": [
                _VisualElementSerialization.to_dict(element)
                for element in self.elements
            ],
            "counts": {
                "picture": counts["picture"],
                "table": counts["table"],
                "math": counts["math"],
            },
        }

    def get_element(self, element_id: str) -> VisualElement | None:
        """Return the visual element with `element_id`, if present."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None


# ================================================================================
# Quote Contracts
# ================================================================================


@dataclass(slots=True)
class QuoteMatch:
    """Result of finding a text occurrence on a page."""

    text: str
    boxes: list[dict[str, Any]]
    image: Image.Image


@dataclass(slots=True)
class VisualElementMatch:
    """Result of finding a visual element on a page."""

    id: str
    element_type: VisualElementType
    bbox: dict[str, Any]
    image: Image.Image


# ================================================================================
# Media Contracts
# ================================================================================


@dataclass(slots=True)
class MediaItem:
    """Downloaded or cached media item."""

    url: str
    content: bytes
    content_type: str
    extension: str
    size_bytes: int
    from_cache: bool = False
    timestamp: str | None = None


@dataclass(slots=True)
class MediaCacheEntry:
    """Cached media metadata and content."""

    url: str
    content: bytes
    content_type: str
    extension: str
    size_bytes: int
    timestamp: str | None = None


# ================================================================================
# Response Contracts
# ================================================================================


@dataclass(slots=True)
class ConversionResponse:
    """Response from HTML-to-Markdown conversion."""

    markdown: str
    manifest: VisualElementManifest
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FetchResponse:
    """Response from fetching HTML content."""

    html: str
    url: str
    from_cache: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MediaDownloadResponse:
    """Response from media download operations."""

    items: list[MediaItem]
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        """Return the number of downloaded items."""
        return len(self.items)
