"""MHTML media extraction helpers (used by the optional process pipeline)."""

from __future__ import annotations

import email
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


def _extract_filename_from_url(url: str) -> str:
    """Extract a stable filename from a URL for writing extracted media."""
    parsed = urlparse(url)
    filename = posixpath.basename(parsed.path)
    filename = unquote(filename)
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return filename or "media"


def extract_media_from_mhtml(
    mhtml: str | None,
    output_dir: Path,
    referenced_urls: set[str],
) -> dict[str, str]:
    """Extract referenced media payloads from an MHTML document.

    Returns a mapping from original URL to a relative path under output_dir.
    """
    if not mhtml:
        return {}

    msg = email.message_from_string(mhtml)
    media_dir = output_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    url_mapping: dict[str, str] = {}

    for part in msg.walk():
        content_location = part.get("Content-Location")
        if not content_location:
            continue

        if content_location not in referenced_urls:
            continue

        payload = part.get_payload(decode=True)
        if payload is None:
            continue

        filename = _extract_filename_from_url(content_location)
        filepath = media_dir / filename
        filepath.write_bytes(payload)
        url_mapping[content_location] = str(filepath.relative_to(output_dir))

    return url_mapping


def rewrite_media_urls(content: str, url_mapping: dict[str, str]) -> str:
    """Rewrite referenced URLs in content to their extracted local paths."""
    result = content
    for original_url, local_path in url_mapping.items():
        result = result.replace(original_url, local_path)
    return result


def find_image_urls_in_content(content: str) -> set[str]:
    """Find image URLs referenced in HTML or Markdown content."""
    urls: set[str] = set()

    html_pattern = re.compile(r"src=[\"\']([^\"\']+)[\"\']")
    urls.update(html_pattern.findall(content))

    md_pattern = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
    urls.update(md_pattern.findall(content))

    return urls
