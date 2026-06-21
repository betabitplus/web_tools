"""html_reader service orchestrator.

Internal module (not part of the stable public API).
The stable entrypoint is `web_tools`.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from py_lib_runtime import get_logger, log_operation_duration

from web_tools._api.errors import CrawlError
from web_tools._api.types import VisualElementManifest
from web_tools._internal.html_reader.html_processing import (
    extract_article,
    make_links_absolute,
    sanitize_html,
)
from web_tools._internal.html_reader.markdown import html_to_markdown
from web_tools._internal.html_reader.mhtml_media import (
    extract_media_from_mhtml,
    find_image_urls_in_content,
    rewrite_media_urls,
)
from web_tools._internal.html_reader.visual_elements import annotate_visual_elements
from web_tools._internal.page_artifacts.fetch import fetch_html

logger = get_logger(__name__)


def html2html(html: str, *, base_url: str | None = None) -> str:
    """Extract readable article HTML and sanitize it (optional absolute links)."""
    article_html = extract_article(html)
    if base_url:
        article_html = make_links_absolute(article_html, base_url)
    return sanitize_html(article_html)


def html2md(
    html: str, base_url: str | None = None
) -> tuple[str, VisualElementManifest]:
    """Convert HTML to Markdown and annotate detected visual elements."""
    clean_html = html2html(html, base_url=base_url)
    markdown = html_to_markdown(clean_html)
    return annotate_visual_elements(markdown)


@log_operation_duration(logger, event_type="web_tools.process.completed")
async def process_url(
    url: str,
    output_dir: Path,
    timeout_sec: float,
    *,
    no_cache: bool = False,
) -> None:
    """Optional processing pipeline for content extraction."""
    try:
        crawl_result = await fetch_html(
            url,
            force_refresh=False,
            no_cache=no_cache,
            timeout_sec=timeout_sec,
        )
    except CrawlError as e:
        logger.exception(
            "Failed to fetch HTML.",
            event_type="web_tools.fetch.failed",
            url=url,
            error={"message": str(e), "type": type(e).__name__},
            exc_info=e,
        )
        raise

    raw_html = crawl_result.html
    final_url = crawl_result.url
    mhtml = crawl_result.mhtml

    await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)

    logger.info(
        "[4/5] Generating outputs...",
        event_type="web_tools.output.generate.started",
        url=final_url,
    )
    html_content = html2html(raw_html, base_url=final_url)
    md_content, _ = html2md(raw_html, base_url=final_url)

    referenced_urls = find_image_urls_in_content(html_content)
    referenced_urls.update(find_image_urls_in_content(md_content))

    logger.info(
        "[5/5] Extracting referenced media from MHTML...",
        event_type="web_tools.media.extract.started",
        url=final_url,
    )
    url_mapping = extract_media_from_mhtml(mhtml, output_dir, referenced_urls)
    logger.info(
        "Media extraction completed",
        event_type="web_tools.media.extract.completed",
        extracted_count=len(url_mapping),
        referenced_count=len(referenced_urls),
    )

    if url_mapping:
        html_content = rewrite_media_urls(html_content, url_mapping)
        md_content = rewrite_media_urls(md_content, url_mapping)

    await asyncio.to_thread(
        (output_dir / "article.html").write_text,
        html_content,
        encoding="utf-8",
    )
    await asyncio.to_thread(
        (output_dir / "article.md").write_text,
        md_content,
        encoding="utf-8",
    )

    logger.info(
        "Output saved",
        event_type="web_tools.output.saved",
        output_dir=output_dir,
    )
