"""Supported public package entrypoint for `web_tools`.

Why:
    Exposes the stable public surface from one import boundary.

What belongs here:
    Re-exports of facade functions/classes, public DTOs, config objects,
    vocabulary types, public exceptions, and package version.

What does not belong here:
    Raw defaults, private runtime helpers, browser/cache internals, stores, or
    other implementation details.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from web_tools._api.cache import configure_cache
from web_tools._api.config import (
    MediaConfig,
    WebToolsConfig,
    get_web_tools_config,
    install_web_tools_config,
)
from web_tools._api.errors import (
    CacheError,
    ConversionError,
    CrawlError,
    InvalidConfigValueError,
    InvalidElementIdError,
    MediaDownloadError,
    QuoteError,
    ScriptNotFoundError,
    WebToolsConfigurationError,
    WebToolsError,
    WebToolsProviderError,
    WebToolsUsageError,
    WebToolsValidationError,
)
from web_tools._api.html import fetch_html, html2html, html2md
from web_tools._api.media import MediaDownloader
from web_tools._api.quoting import quote_element, quote_text
from web_tools._api.types import (
    ConversionResponse,
    FetchResponse,
    MediaCacheEntry,
    MediaDownloadResponse,
    MediaItem,
    MediaType,
    QuoteMatch,
    VisualElement,
    VisualElementManifest,
    VisualElementMatch,
    VisualElementType,
)

try:
    __version__ = version("web-tools")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+local"

__all__ = [
    "CacheError",
    "ConversionError",
    "ConversionResponse",
    "CrawlError",
    "FetchResponse",
    "InvalidConfigValueError",
    "InvalidElementIdError",
    "MediaCacheEntry",
    "MediaConfig",
    "MediaDownloadError",
    "MediaDownloadResponse",
    "MediaDownloader",
    "MediaItem",
    "MediaType",
    "QuoteError",
    "QuoteMatch",
    "ScriptNotFoundError",
    "VisualElement",
    "VisualElementManifest",
    "VisualElementMatch",
    "VisualElementType",
    "WebToolsConfig",
    "WebToolsConfigurationError",
    "WebToolsError",
    "WebToolsProviderError",
    "WebToolsUsageError",
    "WebToolsValidationError",
    "__version__",
    "configure_cache",
    "fetch_html",
    "get_web_tools_config",
    "html2html",
    "html2md",
    "install_web_tools_config",
    "quote_element",
    "quote_text",
]
