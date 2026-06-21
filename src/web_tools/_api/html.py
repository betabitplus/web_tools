"""Public HTML fetching and conversion facades.

Why:
    Keeps the supported HTML function signatures visible while private runtime
    code owns crawling, caching, conversion, and response assembly.
"""

from __future__ import annotations

from web_tools._api.types import ConversionResponse, FetchResponse
from web_tools._internal import (
    build_fetch_response,
    build_markdown_response,
    build_readable_html,
)

# ================================================================================
# Public API
# ================================================================================


def html2html(html: str, *, base_url: str | None = None) -> str:
    """Convert raw HTML to readable, sanitized HTML."""
    return build_readable_html(html, base_url=base_url)


def html2md(html: str, *, base_url: str | None = None) -> ConversionResponse:
    """Convert HTML to Markdown with a visual element manifest."""
    return build_markdown_response(html, base_url=base_url)


async def fetch_html(
    url: str,
    *,
    force_refresh: bool = False,
    no_cache: bool = False,
    timeout_sec: float | None = None,
) -> FetchResponse:
    """Fetch and cache HTML from a URL."""
    return await build_fetch_response(
        url=url,
        force_refresh=force_refresh,
        no_cache=no_cache,
        timeout_sec=timeout_sec,
    )
