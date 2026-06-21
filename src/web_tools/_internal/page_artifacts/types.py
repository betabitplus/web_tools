"""Types for raw page artifacts.

Internal module (not part of the stable public API).
"""

from __future__ import annotations


class PageArtifacts:
    """Raw artifacts captured while fetching a page."""

    def __init__(
        self,
        html: str,
        url: str,
        mhtml: str | None = None,
        screenshot: bytes | None = None,
    ) -> None:
        """Create a page artifact bundle.

        Args:
            html: The page HTML.
            url: The final URL (after any redirects).
            mhtml: Optional MHTML snapshot.
            screenshot: Optional screenshot bytes.
        """
        self.html = html
        self.url = url
        self.mhtml = mhtml
        self.screenshot = screenshot


# Backward-compatible internal alias for older naming.
CrawlResult = PageArtifacts
