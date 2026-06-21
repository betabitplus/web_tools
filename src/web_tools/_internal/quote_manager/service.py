"""quote_manager service orchestrator.

Internal module (not part of the stable public API).
The stable entrypoint is `web_tools`.
"""

from __future__ import annotations

from pathlib import Path

from fake_useragent import UserAgent
from PIL import Image
from playwright.async_api import Page, async_playwright
from py_lib_runtime import get_logger, log_operation_duration

from web_tools._api.errors import CrawlError, QuoteError, ScriptNotFoundError
from web_tools._api.types import QuoteMatch, VisualElementMatch
from web_tools._internal.config import get_default_web_tools_resolver
from web_tools._internal.quote_manager.playwright_loader import (
    load_page_from_cache_entry,
    load_page_live,
    reset_page_state,
    scroll_selection_into_view,
    wait_for_network_idle,
)
from web_tools._internal.quote_manager.quote_capture import (
    annotate_screenshot_with_boxes,
    capture_viewport_screenshot,
    extract_match_boxes,
    find_next_match,
    find_visual_element_on_page,
)
from web_tools._internal.quote_manager.quote_validation import parse_element_id
from web_tools._internal.quote_manager.text_normalization import (
    generate_search_variants,
    md_to_plaintext,
)

logger = get_logger(__name__)

_WORD_BOX_SCRIPT = (
    Path(__file__).resolve().parent.parent / "quote_manager" / "extract_word_boxes.js"
)


def _resolve_user_agent(config_user_agent: str | None) -> str:
    """Resolve a user-agent string, falling back to a random one."""
    if config_user_agent:
        return config_user_agent
    return UserAgent().random


async def _ensure_page_loaded(
    page: Page,
    url: str,
    *,
    force_refresh: bool = False,
    timeout_sec: float,
    wait_for_network: bool = False,
) -> None:
    """Load a page from cached MHTML when possible, otherwise live."""
    from web_tools._internal.page_artifacts.cache import get_page_artifacts_cache
    from web_tools._internal.page_artifacts.fetch import fetch_html

    if get_page_artifacts_cache({}) is None:
        await load_page_live(page, url, timeout_sec)
        if wait_for_network:
            await wait_for_network_idle(page)
        return

    result = await fetch_html(url, force_refresh=force_refresh, timeout_sec=timeout_sec)

    if not result.mhtml and not force_refresh:
        result = await fetch_html(url, force_refresh=True, timeout_sec=timeout_sec)

    if result.mhtml:
        await load_page_from_cache_entry(page, result.mhtml, url)
    else:
        await load_page_live(page, url, timeout_sec)

    if wait_for_network:
        await wait_for_network_idle(page)


async def _find_matches_on_page(page: Page, text: str) -> list[QuoteMatch]:
    """Find matches for the text on the loaded page and capture screenshots."""
    if not _WORD_BOX_SCRIPT.exists():
        raise ScriptNotFoundError(path=_WORD_BOX_SCRIPT)

    js_script = _WORD_BOX_SCRIPT.read_text()
    matches: list[QuoteMatch] = []

    plaintext = md_to_plaintext(text)
    search_variants = generate_search_variants(plaintext)

    await page.evaluate(
        """
        (() => {
            const style = document.createElement('style');
            style.textContent = `
                ::selection {
                    background: transparent !important;
                    color: inherit !important;
                }
            `;
            document.head.appendChild(style);
        })()
        """
    )

    for search_text in search_variants:
        await reset_page_state(page)

        while await find_next_match(page, search_text):
            await scroll_selection_into_view(page)
            match_data = await extract_match_boxes(page, js_script)

            if not match_data or not match_data.get("boxes"):
                continue

            screenshot = await capture_viewport_screenshot(page)
            image: Image.Image = annotate_screenshot_with_boxes(
                screenshot, match_data["boxes"]
            )
            matches.append(
                QuoteMatch(text=text, boxes=match_data["boxes"], image=image)
            )

        if matches:
            break

    return matches


@log_operation_duration(logger, event_type="web_tools.quote.text.completed")
async def quote_text(
    url: str,
    text: str,
    *,
    force_refresh: bool = False,
    timeout_sec: float | None = None,
) -> list[QuoteMatch]:
    """Find occurrences of `text` on a page and return annotated screenshots."""
    resolver = get_default_web_tools_resolver()
    config_timeout = resolver.resolve_timeout(timeout_sec)
    viewport_width, viewport_height = resolver.resolve_viewport()
    user_agent = resolver.resolve_user_agent(None)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(user_agent=_resolve_user_agent(user_agent))
        page = await context.new_page()
        await page.set_viewport_size(
            {"width": viewport_width, "height": viewport_height}
        )

        try:
            await _ensure_page_loaded(
                page, url, force_refresh=force_refresh, timeout_sec=config_timeout
            )
        except CrawlError as e:
            await browser.close()
            raise QuoteError(url=url, text=text, cause=e) from e

        matches = await _find_matches_on_page(page, text)
        await browser.close()

    return matches


@log_operation_duration(logger, event_type="web_tools.quote.element.completed")
async def quote_element(
    element_id: str,
    url: str,
    *,
    force_refresh: bool = False,
    timeout_sec: float | None = None,
) -> VisualElementMatch | None:
    """Locate a visual element by id and return a screenshot of it."""
    resolver = get_default_web_tools_resolver()
    config_timeout = resolver.resolve_timeout(timeout_sec)
    viewport_width, viewport_height = resolver.resolve_viewport()
    user_agent = resolver.resolve_user_agent(None)

    element_type, selector, index = parse_element_id(element_id)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(user_agent=_resolve_user_agent(user_agent))
        page = await context.new_page()
        await page.set_viewport_size(
            {"width": viewport_width, "height": viewport_height}
        )

        try:
            await _ensure_page_loaded(
                page,
                url,
                force_refresh=force_refresh,
                timeout_sec=config_timeout,
                wait_for_network=True,
            )
        except CrawlError as e:
            await browser.close()
            raise QuoteError(url=url, element_id=element_id, cause=e) from e

        match = await find_visual_element_on_page(
            page,
            element_id=element_id,
            element_type=element_type,
            selector=selector,
            index=index,
        )
        await browser.close()

    return match
