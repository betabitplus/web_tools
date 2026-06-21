"""Crawling primitives for page artifact capture.

Internal module (not part of the stable public API).
"""

from __future__ import annotations

import base64

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from py_lib_runtime import get_logger, log_operation_duration

from web_tools._api.errors import CrawlError
from web_tools._internal.config import get_default_web_tools_resolver
from web_tools._internal.page_artifacts.types import PageArtifacts

logger = get_logger(__name__)


@log_operation_duration(logger, event_type="web_tools.crawl.completed")
async def crawl_url(
    url: str,
    *,
    timeout_sec: float | None = None,
    capture_cache: bool = False,
) -> PageArtifacts:
    """Crawl a URL using a headless browser and capture optional artifacts."""
    resolver = get_default_web_tools_resolver()
    timeout_sec = resolver.resolve_timeout(timeout_sec)

    logger.info(
        "Page crawl started",
        event_type="web_tools.crawl.started",
        url=url,
        timeout_sec=timeout_sec,
    )

    config = CrawlerRunConfig(
        screenshot=capture_cache,
        capture_mhtml=capture_cache,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url, config=config, bypass_cache=True)
        if not result.success:
            raise CrawlError(url=url, reason=result.error_message)

        screenshot_bytes = None
        if capture_cache and result.screenshot:
            screenshot_bytes = base64.b64decode(result.screenshot)

        return PageArtifacts(
            html=result.html,
            url=result.url,
            mhtml=result.mhtml if capture_cache else None,
            screenshot=screenshot_bytes,
        )
