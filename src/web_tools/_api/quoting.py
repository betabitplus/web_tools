"""Public quoting facades.

Why:
    Keeps text and visual-element quoting signatures visible while browser,
    timeout, cache, and screenshot mechanics stay private.
"""

from __future__ import annotations

from web_tools._api.types import QuoteMatch, VisualElementMatch
from web_tools._internal import (
    build_quote_element_match,
    build_quote_text_matches,
)

# ================================================================================
# Public API
# ================================================================================


async def quote_text(
    text: str,
    url: str,
    *,
    force_refresh: bool = False,
    timeout_sec: float | None = None,
) -> list[QuoteMatch]:
    """Find text occurrences on a webpage and return annotated screenshots."""
    return await build_quote_text_matches(
        text=text,
        url=url,
        force_refresh=force_refresh,
        timeout_sec=timeout_sec,
    )


async def quote_element(
    element_id: str,
    url: str,
    *,
    force_refresh: bool = False,
    timeout_sec: float | None = None,
) -> VisualElementMatch | None:
    """Find a visual element by ID and return an annotated screenshot."""
    return await build_quote_element_match(
        element_id=element_id,
        url=url,
        force_refresh=force_refresh,
        timeout_sec=timeout_sec,
    )
