"""Private runtime backing for public facade modules.

Why:
    Keeps `_api` modules focused on public signatures while runtime default
    resolution, cache inspection, and response assembly stay private.
"""

from __future__ import annotations

from pathlib import Path

from web_tools._api.types import (
    ConversionResponse,
    FetchResponse,
    QuoteMatch,
    VisualElementMatch,
)
from web_tools._internal.cache.manager import (
    configure_cache as configure_page_cache,
    get_cache as page_cache,
)
from web_tools._internal.html_reader.service import (
    html2html as render_readable_html,
    html2md as render_markdown_parts,
)
from web_tools._internal.page_artifacts.fetch import fetch_html as fetch_page_artifacts
from web_tools._internal.quote_manager.service import (
    quote_element as capture_visual_element,
    quote_text as capture_text_matches,
)

# ================================================================================
# Cache Runtime
# ================================================================================


def configure_page_cache_from_user_path(cache_dir: str | Path | None) -> None:
    """Configure page cache storage from a caller-provided path."""
    path = None if cache_dir is None else Path(cache_dir).expanduser()
    configure_page_cache(path)


# ================================================================================
# HTML Runtime
# ================================================================================


def build_readable_html(html: str, *, base_url: str | None = None) -> str:
    """Return readable sanitized HTML for public callers."""
    return render_readable_html(html, base_url=base_url)


def build_markdown_response(
    html: str,
    *,
    base_url: str | None = None,
) -> ConversionResponse:
    """Return the public Markdown conversion response."""
    markdown, manifest = render_markdown_parts(html, base_url)
    return ConversionResponse(markdown=markdown, manifest=manifest)


async def build_fetch_response(
    url: str,
    *,
    force_refresh: bool = False,
    no_cache: bool = False,
    timeout_sec: float | None = None,
) -> FetchResponse:
    """Return fetched HTML with public cache-hit evidence."""
    from_cache = False
    if not (force_refresh or no_cache):
        cache = page_cache()
        from_cache = cache is not None and cache.has(url)

    result = await fetch_page_artifacts(
        url=url,
        force_refresh=force_refresh,
        no_cache=no_cache,
        timeout_sec=timeout_sec,
    )
    return FetchResponse(html=result.html, url=result.url, from_cache=from_cache)


# ================================================================================
# Quoting Runtime
# ================================================================================


async def build_quote_text_matches(
    text: str,
    url: str,
    *,
    force_refresh: bool = False,
    timeout_sec: float | None = None,
) -> list[QuoteMatch]:
    """Return public text quote matches for one page."""
    return await capture_text_matches(
        url=url,
        text=text,
        force_refresh=force_refresh,
        timeout_sec=timeout_sec,
    )


async def build_quote_element_match(
    element_id: str,
    url: str,
    *,
    force_refresh: bool = False,
    timeout_sec: float | None = None,
) -> VisualElementMatch | None:
    """Return one public visual-element quote match when found."""
    return await capture_visual_element(
        element_id=element_id,
        url=url,
        force_refresh=force_refresh,
        timeout_sec=timeout_sec,
    )
