"""HTML conversion public-contract properties.

Why:
    Protects generated invariants for readable HTML, Markdown conversion, and
    public visual manifest IDs.

Covers:
    Area: HTML conversion and visual manifest
    Behavior: generated article content, Markdown output, picture manifest IDs
    Interface: `html2html(...)`, `html2md(...)`, and `ConversionResponse`

Checks:
    If generated article HTML is converted to readable HTML, then generated
    article text remains caller-visible.
    If generated article HTML contains image elements, then the public
    conversion response exposes matching picture counts and `P_N` IDs.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

from web_tools import ConversionResponse, VisualElementType, html2html, html2md

# =============================================================================
# Strategies
# =============================================================================

_PROPERTY_SETTINGS = settings(max_examples=30)

_SAFE_WORD = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=16,
)
_IMAGE_COUNT = st.integers(min_value=0, max_value=4)


# =============================================================================
# Helpers
# =============================================================================


def build_article_html(*, title: str, body: str, image_count: int) -> str:
    """Build simple generated article HTML with optional pictures."""
    image_html = "".join(
        f'<img src="/generated-{index}.png" alt="Image {index}">'
        for index in range(image_count)
    )
    return f"""
    <html>
      <body>
        <nav>Navigation should not be the main article.</nav>
        <article>
          <h1>{title}</h1>
          <p>{body}</p>
          {image_html}
        </article>
      </body>
    </html>
    """


# =============================================================================
# Assertions
# =============================================================================


def assert_readable_html_preserves_article_text(
    readable_html: str,
    *,
    title: str,
    body: str,
) -> None:
    """Assert generated article text survives public readable conversion."""
    # The readable output may change parser details, but generated article text
    # should stay present for callers.
    assert title in readable_html
    assert body in readable_html


def assert_conversion_manifest(
    response: ConversionResponse,
    *,
    title: str,
    body: str,
    image_count: int,
) -> None:
    """Assert generated Markdown and picture manifest evidence."""
    # First prove the response crossed the public boundary as the documented DTO.
    assert isinstance(response, ConversionResponse)
    assert title in response.markdown
    assert body in response.markdown

    # Then prove generated pictures become public P_N handles.
    assert response.manifest.counts == {
        "total": image_count,
        "picture": image_count,
        "table": 0,
        "math": 0,
    }
    assert [element.id for element in response.manifest.elements] == [
        f"P_{index}" for index in range(image_count)
    ]
    assert all(
        element.element_type == VisualElementType.PICTURE
        for element in response.manifest.elements
    )


# =============================================================================
# Properties
# =============================================================================


@_PROPERTY_SETTINGS
@given(title=_SAFE_WORD, body=_SAFE_WORD, image_count=_IMAGE_COUNT)
def test_generated_html_conversion_preserves_public_manifest_contract(
    *,
    title: str,
    body: str,
    image_count: int,
) -> None:
    """Generated article HTML should produce stable public conversion evidence."""
    html = build_article_html(title=title, body=body, image_count=image_count)

    readable_html = html2html(html, base_url="https://example.com/articles/")
    response = html2md(html, base_url="https://example.com/articles/")

    assert_readable_html_preserves_article_text(
        readable_html,
        title=title,
        body=body,
    )
    assert_conversion_manifest(
        response,
        title=title,
        body=body,
        image_count=image_count,
    )
