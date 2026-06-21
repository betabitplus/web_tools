# %%
"""Workbench scenario: HTML conversion and visual manifest.

Why:
    Isolates the readability, Markdown, and visual-manifest concept on a live
    page without importing shipped `web_tools` code.

Covers:
    Area: HTML conversion and visual manifest
    Behavior: live HTML fetch, readable extraction, Markdown output, visual IDs
    Interface: `httpx`, `readability.Document`, `Cleaner`, `HTML2Text`, and `lxml`

Checks:
    If live page HTML is converted to readable HTML, then the page heading
    remains and navigation-free Markdown is produced.
    If visual elements are extracted from readable HTML, then picture and table
    IDs are stable public handles.
    If the manifest is serialized, then counts stay in caller-facing
    vocabulary instead of parser-native objects.

Examples:
    Run manually:
        uv run python -m workbench.web_tools.html_conversion_and_visual_manifest
        uv run py-lib-reproduce-running-loop \
            workbench.web_tools.html_conversion_and_visual_manifest
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import html2text
import httpx
from lxml import html
from lxml_html_clean import Cleaner
from py_lib_tooling import console
from readability import Document

# =============================================================================
# Scenario
# =============================================================================

TEST_URL = "https://w3schoolsua.github.io/html/html_tables_en.html#gsc.tab=0"


class VisualElementType(StrEnum):
    """Stable visual element vocabulary for this isolated probe."""

    PICTURE = "picture"
    TABLE = "table"
    MATH = "math"


@dataclass(frozen=True, slots=True)
class VisualElement:
    """One public visual handle extracted from converted HTML."""

    id: str
    element_type: VisualElementType
    label: str


@dataclass(frozen=True, slots=True)
class VisualManifest:
    """Caller-facing visual element manifest for this isolated probe."""

    elements: tuple[VisualElement, ...]

    @property
    def counts(self) -> dict[str, int]:
        """Return stable category counts for manual verification."""
        return {
            "total": len(self.elements),
            "picture": sum(
                element.element_type == VisualElementType.PICTURE
                for element in self.elements
            ),
            "table": sum(
                element.element_type == VisualElementType.TABLE
                for element in self.elements
            ),
            "math": sum(
                element.element_type == VisualElementType.MATH
                for element in self.elements
            ),
        }


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Markdown plus manifest evidence produced by the isolated probe."""

    markdown: str
    manifest: VisualManifest
    metadata: dict[str, str]


# =============================================================================
# Helpers
# =============================================================================


def _to_markdown(readable_html: str) -> str:
    """Convert readable HTML to Markdown with stable wrapping."""
    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_links = False
    return converter.handle(readable_html).strip()


def _fetch_live_html(url: str) -> tuple[str, str]:
    """Fetch live HTML and return the final URL used for metadata."""
    response = httpx.get(url, follow_redirects=True, timeout=15)
    response.raise_for_status()
    return response.text, str(response.url)


def _build_manifest(readable_html: str) -> VisualManifest:
    """Extract public visual IDs from the readable HTML artifact."""
    tree = html.fromstring(readable_html)
    elements: list[VisualElement] = []

    for index, image in enumerate(tree.xpath("//img")):
        label = image.get("alt") or image.get("src") or f"picture {index}"
        elements.append(
            VisualElement(
                id=f"P_{index}",
                element_type=VisualElementType.PICTURE,
                label=label,
            )
        )

    for index, table in enumerate(tree.xpath("//table")):
        heading = " ".join(table.xpath(".//th/text()")).strip()
        elements.append(
            VisualElement(
                id=f"T_{index}",
                element_type=VisualElementType.TABLE,
                label=heading or f"table {index}",
            )
        )

    return VisualManifest(elements=tuple(elements))


def _serialize_element(element: VisualElement) -> dict[str, str]:
    """Serialize one manifest element without exposing parser objects."""
    return {
        "id": element.id,
        "element_type": element.element_type,
        "label": element.label,
    }


def _serialize_result(result: ConversionResult) -> dict[str, Any]:
    """Serialize stable conversion evidence for manual output."""
    return {
        "markdown_length": len(result.markdown),
        "markdown_has_heading": "HTML Tables" in result.markdown,
        "manifest_counts": result.manifest.counts,
        "manifest_ids": [element.id for element in result.manifest.elements],
        "first_elements": [
            _serialize_element(element) for element in result.manifest.elements[:3]
        ],
        "metadata": result.metadata,
    }


# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline(*, html_text: str, base_url: str) -> ConversionResult:
    """Run the isolated HTML conversion and manifest flow."""
    readable_html = Document(html_text).summary()
    cleaned_html = Cleaner(safe_attrs_only=True).clean_html(readable_html)
    markdown = _to_markdown(cleaned_html)
    manifest = _build_manifest(cleaned_html)
    return ConversionResult(
        markdown=markdown,
        manifest=manifest,
        metadata={
            "base_url": base_url,
            "readable_html_length": str(len(cleaned_html)),
            "source": "live_http",
        },
    )


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the workbench script as a narrative manual demo."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Fetching a live table page, then converting it into Markdown and visual IDs.",
        details=(f"url: {TEST_URL}",),
    )

    html_text, final_url = _fetch_live_html(TEST_URL)
    result = run_pipeline(html_text=html_text, base_url=final_url)
    evidence = _serialize_result(result)

    console.demo_step(
        "Observed Conversion",
        "The isolated dependency flow produced Markdown plus manifest evidence.",
        details=(
            f"markdown_length: {evidence['markdown_length']}",
            f"total_elements: {evidence['manifest_counts']['total']}",
        ),
    )
    console.print_json(evidence)
    console.rule("[header]MARKDOWN PREVIEW (first 500 chars)[/]")
    console.print(result.markdown[:500])
    console.demo_outcome(
        "The conversion concept returns readable text and stable visual handles "
        "without coupling workbench to shipped package code.",
    )


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
{
  "first_elements": [
    {
      "element_type": "table",
      "id": "T_0",
      "label": "Company Contact Country"
    }
  ],
  "manifest_counts": {
    "math": 0,
    "picture": 0,
    "table": 2,
    "total": 2
  },
  "manifest_ids": [
    "T_0",
    "T_1"
  ],
  "markdown_has_heading": true,
  "markdown_length": 3671,
  "metadata": {
    "base_url": "https://w3schoolsua.github.io/html/html_tables_en.html#gsc.tab=0",
    "readable_html_length": "9571",
    "source": "live_http"
  }
}
""".strip()
