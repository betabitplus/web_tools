# %%
"""HTML to Markdown conversion e2e.

Why:
    Verifies that public fetching and conversion produce Markdown plus stable
    visual manifest evidence.

Covers:
    Area: HTML conversion and visual manifest
    Behavior: fetched HTML, Markdown output, visual element categories
    Interface: `fetch_html(...)` and `html2md(...)`

Checks:
    If the public fetch returns page HTML, then the public conversion returns
    non-empty Markdown.
    If visual elements are detected, then the serialized response exposes
    counts and table IDs through public manifest fields.

Examples:
    Run manually:
        uv run python -m \
            tests.web_tools.e2e.html_conversion_and_visual_manifest.test_html2md_pipeline

    Run as test:
        pytest \
            tests/web_tools/e2e/html_conversion_and_visual_manifest/test_html2md_pipeline.py
"""

from __future__ import annotations

import pytest
from IPython.display import Markdown, display
from py_lib_tooling import console, run_async
from syrupy.assertion import SnapshotAssertion

from web_tools import (
    ConversionResponse,
    VisualElementManifest,
    VisualElementType,
    fetch_html,
    html2md,
)

pytestmark = [
    pytest.mark.e2e_behavior,
    pytest.mark.e2e_contract,
    pytest.mark.hermetic,
]


# =============================================================================
# Scenario
# =============================================================================

TEST_URL = "https://w3schoolsua.github.io/html/html_tables_en.html#gsc.tab=0"


# =============================================================================
# Helpers
# =============================================================================


async def load_inputs(url: str = TEST_URL) -> dict[str, str]:
    """Load page HTML through the public fetch facade."""
    response = await fetch_html(url)
    return {
        "html": response.html,
        "base_url": url,
    }


def _element_count(
    manifest: VisualElementManifest, element_type: VisualElementType
) -> int:
    """Count public manifest elements of one category."""
    return sum(
        1 for element in manifest.elements if element.element_type == element_type
    )


def serialize_response(response: ConversionResponse) -> dict[str, object]:
    """Serialize public conversion evidence for stable snapshot comparison."""
    manifest = response.manifest
    return {
        "markdown_length": len(response.markdown),
        "markdown_has_content": len(response.markdown) > 100,
        "element_counts": {
            "picture": _element_count(manifest, VisualElementType.PICTURE),
            "table": _element_count(manifest, VisualElementType.TABLE),
            "math": _element_count(manifest, VisualElementType.MATH),
        },
        "table_ids": [
            element.id
            for element in manifest.elements
            if element.element_type == VisualElementType.TABLE
        ],
        "total_elements": len(manifest.elements),
        "metadata": response.metadata,
    }


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, html: str, base_url: str) -> ConversionResponse:
    """Run the public HTML-to-Markdown conversion flow."""
    return html2md(html, base_url=base_url)


# =============================================================================
# Assertions
# =============================================================================


def assert_pipeline_response(
    actual: dict[str, object],
    snapshot: SnapshotAssertion,
) -> None:
    """Assert the public conversion evidence for the scenario."""
    # First prove conversion produced non-trivial caller-visible Markdown.
    assert actual["markdown_has_content"] is True

    # Then compare the stable manifest summary against the committed snapshot.
    assert actual == snapshot


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
async def test_html2md_pipeline_hermetic(
    snapshot: SnapshotAssertion,
    e2e_site_url: str,
) -> None:
    """Verify the public HTML-to-Markdown pipeline."""
    inputs = await load_inputs(e2e_site_url)
    response = run_pipeline(**inputs)
    actual = serialize_response(response)

    assert_pipeline_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


async def main() -> None:
    """Run the e2e scenario as a direct live manual check."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Fetching a table-heavy page, then converting it to Markdown.",
        details=(f"URL: {TEST_URL}",),
    )

    inputs = await load_inputs()
    response = run_pipeline(**inputs)
    serialized = serialize_response(response)
    assert serialized["markdown_has_content"] is True

    console.demo_step(
        "Observed Conversion",
        "The public response contains Markdown and visual manifest evidence.",
        details=(
            f"markdown_length: {serialized['markdown_length']}",
            f"total_elements: {serialized['total_elements']}",
        ),
    )
    console.print_json(serialized)

    console.rule("[header]MARKDOWN PREVIEW (first 1000 chars)[/]")
    display(Markdown(response.markdown[:1000]))
    console.demo_outcome(
        "This proves fetched HTML can become public Markdown and manifest data.",
    )


if __name__ == "__main__":
    run_async(main())

# %%
