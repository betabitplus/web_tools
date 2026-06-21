"""Offline public-contract checks for HTML conversion."""

from __future__ import annotations

from web_tools import ConversionResponse, VisualElementType, html2html, html2md

# =============================================================================
# Tests
# =============================================================================


def test_html2html_keeps_article_content() -> None:
    """Cleaned HTML keeps the readable article content."""
    result = html2html(
        """
        <html>
          <body>
            <nav>Navigation</nav>
            <article><h1>Hello</h1><p>Useful text.</p></article>
          </body>
        </html>
        """,
    )

    assert "Hello" in result
    assert "Useful text." in result


def test_html2md_returns_public_response_contract() -> None:
    """Markdown conversion returns the supported response DTO."""
    response = html2md(
        """
        <article>
          <h1>Hello</h1>
          <p>Useful text.</p>
          <img src="https://example.com/a.png" alt="A">
        </article>
        """,
    )

    assert isinstance(response, ConversionResponse)
    assert "Hello" in response.markdown
    assert response.manifest.counts["picture"] == 1
    assert response.manifest.elements[0].element_type == VisualElementType.PICTURE
