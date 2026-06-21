"""Playwright page loading and page-state helpers."""

from __future__ import annotations

import contextlib
import tempfile
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from py_lib_runtime import get_logger

from web_tools._api.errors import CrawlError

logger = get_logger(__name__)


async def reset_page_state(page: Page) -> None:
    """Reset scroll position and clear any selection."""
    await page.evaluate("window.scrollTo(0, 0)")
    await page.evaluate("window.getSelection().removeAllRanges()")
    await page.evaluate("delete window.__webToolsFindState")


async def scroll_selection_into_view(page: Page) -> None:
    """Scroll the current selection into the viewport center."""
    await page.evaluate(
        """
        (() => {
            const sel = window.getSelection();
            if (!sel || sel.rangeCount === 0) return;
            const range = sel.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            const scrollY = window.scrollY + rect.top
                - (window.innerHeight / 2) + (rect.height / 2);
            window.scrollTo({ top: Math.max(0, scrollY), behavior: 'instant' });
        })()
        """
    )
    await page.wait_for_timeout(100)


async def load_page_live(page: Page, url: str, timeout_sec: float) -> None:
    """Navigate to a live URL."""
    logger.info(
        "Page navigation started",
        event_type="web_tools.page.navigate.started",
        url=url,
        timeout_sec=timeout_sec,
    )
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_sec * 1000)
    except PlaywrightTimeout as e:
        raise CrawlError(url=url, cause=e) from e


async def load_page_from_cache_entry(page: Page, mhtml_content: str, url: str) -> None:
    """Load a page from cached MHTML content via a temporary file."""
    temp_path = Path()
    try:
        with tempfile.NamedTemporaryFile(suffix=".mhtml", delete=False) as tmp:
            tmp.write(mhtml_content.encode("utf-8"))
            temp_path = Path(tmp.name)

        logger.info(
            "Loading cached page",
            event_type="web_tools.cache.hit",
            url=url,
        )

        file_uri = temp_path.absolute().as_uri()
        await page.goto(file_uri, wait_until="domcontentloaded")
    finally:
        with contextlib.suppress(Exception):
            if temp_path and temp_path.exists():
                temp_path.unlink()


async def wait_for_network_idle(page: Page) -> None:
    """Best-effort wait for network idle (suppresses Playwright timeouts)."""
    with contextlib.suppress(PlaywrightTimeout):
        await page.wait_for_load_state("networkidle", timeout=10000)
