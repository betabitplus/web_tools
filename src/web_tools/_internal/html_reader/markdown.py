"""Markdown conversion helpers."""

from __future__ import annotations

import html2text


def html_to_markdown(html: str) -> str:
    """Convert sanitized HTML to Markdown."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.body_width = 0
    return converter.handle(html)
