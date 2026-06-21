"""HTML extraction and sanitization helpers."""

from __future__ import annotations

import lxml.html  # nosec B410 - HTML parsing required for controlled content
from lxml_html_clean import Cleaner  # nosec B410 - Sanitization uses trusted config
from py_lib_runtime import get_logger
from readability import Document

logger = get_logger(__name__)

SAFE_ATTRS = {
    "src",
    "href",
    "alt",
    "title",
    "colspan",
    "rowspan",
    "width",
    "height",
    "controls",
    "poster",
}


def extract_article(html: str) -> str:
    """Extract main article content using Readability."""
    try:
        doc = Document(html)
        return doc.summary()
    except Exception as exc:  # Defensive: readability can fail on malformed HTML.
        logger.warning(
            "Readability failed; returning original HTML.",
            event_type="web_tools.readability.failed",
            error={"message": str(exc), "type": type(exc).__name__},
            exc_info=exc,
        )
        return html


def make_links_absolute(html: str, base_url: str) -> str:
    """Resolve relative links to absolute URLs."""
    try:
        if base_url:
            return lxml.html.make_links_absolute(html, base_url=base_url)
    except Exception as exc:  # Defensive
        logger.debug(
            "Link resolution failed; returning original HTML.",
            event_type="web_tools.links.absolute.failed",
            error={"message": str(exc), "type": type(exc).__name__},
            exc_info=exc,
        )
    return html


def sanitize_html(html: str) -> str:
    """Strip non-essential HTML attributes."""
    try:
        cleaner = Cleaner(safe_attrs_only=True, safe_attrs=SAFE_ATTRS)
        return cleaner.clean_html(html)
    except Exception as exc:  # Defensive
        logger.debug(
            "HTML sanitization failed; returning original HTML.",
            event_type="web_tools.sanitize.failed",
            error={"message": str(exc), "type": type(exc).__name__},
            exc_info=exc,
        )
        return html
