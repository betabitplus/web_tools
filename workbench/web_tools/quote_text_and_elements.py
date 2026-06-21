# %%
"""Workbench scenario: quote text and visual elements.

Why:
    Isolates the browser evidence concept for public text and visual-element
    inputs without importing shipped `web_tools` code.

Covers:
    Area: quote text and elements
    Behavior: text lookup, public element ID lookup, annotated screenshot proof
    Interface: `playwright.async_api` plus `P_N`, `T_N`, and `M_N` IDs

Checks:
    If rendered text is quoted, then the probe returns matched text, a positive
    bounding box, and annotated image metadata.
    If public visual element IDs are quoted, then picture, table, and math
    targets return element evidence with positive bounding boxes.
    If the browser evidence is rendered in a notebook, then each target is
    displayed as its own annotated viewport screenshot.
    If the browser evidence is serialized, then it contains image metadata
    rather than browser handles.

Examples:
    Run manually:
        uv run python -m workbench.web_tools.quote_text_and_elements
        uv run py-lib-reproduce-running-loop \
            workbench.web_tools.quote_text_and_elements

    Run in a notebook:
        from workbench.web_tools.quote_text_and_elements import run_notebook_demo

        result = await run_notebook_demo()
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from importlib import import_module
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw
from playwright.async_api import Page, async_playwright
from py_lib_tooling import console, run_async

# =============================================================================
# Scenario
# =============================================================================

TEST_URL = "https://en.wikipedia.org/wiki/Pythagorean_theorem"
TARGET_TEXT = (
    "The theorem can be written as an equation relating the lengths of the "
    "sides a, b and the hypotenuse c"
)
TARGET_ELEMENT_IDS = ("P_2", "T_0", "M_0")
_PUBLIC_ID_RE = re.compile(r"^(?P<prefix>[PTM])_(?P<index>\d+)$")
_HIGHLIGHT = (220, 38, 38)
_VIEWPORT = {"width": 1280, "height": 1024}


class VisualElementType(StrEnum):
    """Stable visual element vocabulary for this isolated probe."""

    PICTURE = "picture"
    TABLE = "table"
    MATH = "math"


@dataclass(frozen=True, slots=True)
class ImageEvidence:
    """Annotated viewport screenshot plus metadata for serialization."""

    image: Image.Image
    size: tuple[int, int]
    mode: str


@dataclass(frozen=True, slots=True)
class TextQuoteEvidence:
    """Text quote result returned by this isolated probe."""

    text: str
    bbox: dict[str, float]
    rect_count: int
    image: ImageEvidence


@dataclass(frozen=True, slots=True)
class ElementQuoteEvidence:
    """Visual element quote result returned by this isolated probe."""

    id: str
    element_type: VisualElementType
    bbox: dict[str, float]
    image: ImageEvidence


@dataclass(frozen=True, slots=True)
class QuoteDemoResult:
    """Complete quote evidence returned by the isolated browser flow."""

    text_quote: TextQuoteEvidence
    element_quotes: tuple[ElementQuoteEvidence | None, ...]


# =============================================================================
# Helpers
# =============================================================================


def _normalize_bbox(raw_bbox: dict[str, float]) -> dict[str, float]:
    """Round browser coordinates to stable manual evidence."""
    return {
        "x": round(raw_bbox["x"], 2),
        "y": round(raw_bbox["y"], 2),
        "width": round(raw_bbox["width"], 2),
        "height": round(raw_bbox["height"], 2),
    }


def _clamp_bbox_to_image(
    bbox: dict[str, float],
    image: Image.Image,
) -> tuple[float, float, float, float]:
    """Clamp a viewport-relative bbox so annotation stays inside the image."""
    x = max(bbox["x"], 0)
    y = max(bbox["y"], 0)
    right = min(x + bbox["width"], image.width)
    bottom = min(y + bbox["height"], image.height)
    return x, y, right, bottom


async def _annotate_viewport_screenshot(
    page: Page,
    viewport_bbox: dict[str, float],
) -> ImageEvidence:
    """Draw the target on the current viewport screenshot."""
    screenshot = await page.screenshot(full_page=False)
    image = Image.open(BytesIO(screenshot)).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        _clamp_bbox_to_image(viewport_bbox, image),
        outline=_HIGHLIGHT,
        width=4,
    )
    return ImageEvidence(image=image, size=image.size, mode=image.mode)


async def _find_text_bbox(page: Page, text: str) -> dict[str, Any]:
    """Return selected text evidence using the browser selection engine."""
    found = await page.evaluate(
        """
        (text) => {
            const selection = window.getSelection();
            selection.removeAllRanges();
            const found = window.find(
                text,
                false,
                false,
                true,
                false,
                true,
                false
            );
            return found && selection.rangeCount > 0;
        }
        """,
        text,
    )
    if found is not True:
        msg = f"Could not find quoted text: {text!r}."
        raise AssertionError(msg)

    await page.evaluate(
        """
        () => {
            const selection = window.getSelection();
            if (!selection || selection.rangeCount === 0) return;
            const rect = selection.getRangeAt(0).getBoundingClientRect();
            const targetTop = (
                window.scrollY
                + rect.top
                - (window.innerHeight / 2)
                + (rect.height / 2)
            );
            window.scrollTo({
                top: Math.max(0, targetTop),
                behavior: 'instant'
            });
        }
        """
    )
    await page.wait_for_timeout(100)

    result = await page.evaluate(
        """
        () => {
            const selection = window.getSelection();
            if (!selection || selection.rangeCount === 0) return null;
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            const rects = Array.from(range.getClientRects());
            return {
                text: selection.toString(),
                rect_count: rects.length,
                bbox: {
                    x: rect.x + window.scrollX,
                    y: rect.y + window.scrollY,
                    width: rect.width,
                    height: rect.height
                },
                viewport_bbox: {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                }
            };
        }
        """
    )
    if not isinstance(result, dict):
        msg = "Browser text lookup returned unexpected evidence."
        raise TypeError(msg)
    return result


def _parse_element_id(element_id: str) -> tuple[VisualElementType, int]:
    """Translate a public element ID into the local selector plan."""
    match = _PUBLIC_ID_RE.fullmatch(element_id)
    if match is None:
        msg = f"Invalid public element ID: {element_id!r}."
        raise ValueError(msg)

    prefix = match.group("prefix")
    index = int(match.group("index"))
    element_type = {
        "P": VisualElementType.PICTURE,
        "T": VisualElementType.TABLE,
        "M": VisualElementType.MATH,
    }[prefix]
    return element_type, index


def _selector_for_type(element_type: VisualElementType) -> str:
    """Return the browser selector for one public visual element category."""
    if element_type == VisualElementType.PICTURE:
        return "main img:not(.mwe-math-fallback-image-inline)"
    if element_type == VisualElementType.TABLE:
        return "main table"
    return "main img.mwe-math-fallback-image-inline"


async def _find_element_bbox(
    page: Page,
    *,
    selector: str,
    index: int,
) -> dict[str, Any] | None:
    """Scroll one visible element into view and return bbox evidence."""
    result = await page.evaluate(
        """
        ([selector, targetIndex]) => {
            const elements = document.querySelectorAll(selector);
            let visibleIndex = 0;
            for (const el of elements) {
                const before = el.getBoundingClientRect();
                if (before.width === 0 || before.height === 0) continue;
                if (visibleIndex === targetIndex) {
                    el.scrollIntoView({
                        block: 'center',
                        inline: 'nearest',
                        behavior: 'instant'
                    });
                    const rect = el.getBoundingClientRect();
                    return {
                        bbox: {
                            x: rect.left + window.scrollX,
                            y: rect.top + window.scrollY,
                            width: rect.width,
                            height: rect.height
                        },
                        viewport_bbox: {
                            x: rect.left,
                            y: rect.top,
                            width: rect.width,
                            height: rect.height
                        }
                    };
                }
                visibleIndex++;
            }
            return null;
        }
        """,
        [selector, index],
    )
    await page.wait_for_timeout(100)
    return result if isinstance(result, dict) else None


def _serialize_text_quote(evidence: TextQuoteEvidence) -> dict[str, Any]:
    """Serialize text quote evidence without leaking browser handles."""
    return {
        "text": evidence.text,
        "bbox": evidence.bbox,
        "bbox_has_positive_size": (
            evidence.bbox["width"] > 0 and evidence.bbox["height"] > 0
        ),
        "rect_count": evidence.rect_count,
        "image_size": list(evidence.image.size),
        "image_mode": evidence.image.mode,
    }


def _serialize_element_quote(evidence: ElementQuoteEvidence | None) -> dict[str, Any]:
    """Serialize visual element quote evidence."""
    if evidence is None:
        return {"found": False}

    return {
        "found": True,
        "id": evidence.id,
        "element_type": evidence.element_type,
        "bbox": evidence.bbox,
        "bbox_has_positive_size": (
            evidence.bbox["width"] > 0 and evidence.bbox["height"] > 0
        ),
        "image_size": list(evidence.image.size),
        "image_mode": evidence.image.mode,
    }


def serialize_result(result: QuoteDemoResult) -> dict[str, object]:
    """Serialize browser evidence into stable JSON-friendly output."""
    return {
        "text_quote": _serialize_text_quote(result.text_quote),
        "element_quotes": [
            _serialize_element_quote(evidence) for evidence in result.element_quotes
        ],
    }


def _is_notebook_output() -> bool:
    """Return whether the current IPython shell can display rich images."""
    try:
        get_ipython = _load_ipython_getter()
    except ModuleNotFoundError:
        return False

    shell = get_ipython()
    return bool(shell and shell.__class__.__name__ != "TerminalInteractiveShell")


def _load_ipython_getter() -> Callable[[], object | None]:
    """Load IPython lazily so workbench keeps dependency checks clean."""
    module = import_module("IPython.core.getipython")
    getter = module.get_ipython
    if not callable(getter):
        msg = "IPython.core.getipython.get_ipython is not callable."
        raise TypeError(msg)
    return getter


def _display_markdown(text: str) -> None:
    """Display a Markdown heading in notebook environments."""
    display_module = import_module("IPython.display")
    display = display_module.display
    markdown = display_module.Markdown
    display(markdown(text))


def _display_image(image: Image.Image) -> None:
    """Display a PIL image in notebook environments."""
    display_module = import_module("IPython.display")
    display = display_module.display
    display(image)


def display_notebook_images(result: QuoteDemoResult) -> None:
    """Display each annotated screenshot directly in a notebook."""
    if not _is_notebook_output():
        return

    _display_markdown("#### Text quote")
    _display_image(result.text_quote.image.image)

    for evidence in result.element_quotes:
        if evidence is None:
            continue
        _display_markdown(f"#### Element quote: `{evidence.id}`")
        _display_image(evidence.image.image)


# =============================================================================
# Pipeline
# =============================================================================


async def quote_text(page: Page, text: str) -> TextQuoteEvidence:
    """Quote rendered text and return screenshot evidence."""
    raw = await _find_text_bbox(page, text)
    bbox = _normalize_bbox(raw["bbox"])
    viewport_bbox = _normalize_bbox(raw["viewport_bbox"])
    image = await _annotate_viewport_screenshot(page, viewport_bbox)
    return TextQuoteEvidence(
        text=raw["text"],
        bbox=bbox,
        rect_count=raw["rect_count"],
        image=image,
    )


async def quote_element(
    page: Page,
    element_id: str,
) -> ElementQuoteEvidence | None:
    """Quote one public visual element ID and return screenshot evidence."""
    element_type, index = _parse_element_id(element_id)
    selector = _selector_for_type(element_type)
    raw = await _find_element_bbox(page, selector=selector, index=index)
    if raw is None:
        return None

    bbox = _normalize_bbox(raw["bbox"])
    viewport_bbox = _normalize_bbox(raw["viewport_bbox"])
    image = await _annotate_viewport_screenshot(page, viewport_bbox)
    return ElementQuoteEvidence(
        id=element_id,
        element_type=element_type,
        bbox=bbox,
        image=image,
    )


async def run_pipeline(*, url: str) -> QuoteDemoResult:
    """Run the isolated text and element quote flow."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(
            viewport=_VIEWPORT,
            device_scale_factor=1,
        )
        try:
            await page.goto(url, wait_until="load")
            text_evidence = await quote_text(page, TARGET_TEXT)
            element_evidence = [
                await quote_element(page, element_id)
                for element_id in TARGET_ELEMENT_IDS
            ]
        finally:
            await browser.close()

    return QuoteDemoResult(
        text_quote=text_evidence,
        element_quotes=tuple(element_evidence),
    )


async def run_notebook_demo(*, url: str = TEST_URL) -> QuoteDemoResult:
    """Run the quote flow and display annotated screenshots in IPython."""
    result = await run_pipeline(url=url)
    console.print_json(serialize_result(result))
    display_notebook_images(result)
    return result


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


async def main() -> None:
    """Run the workbench script as a narrative manual demo."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Opening a live encyclopedia page in Chromium and quoting text plus "
        "picture, table, and math element IDs.",
        details=(f"url: {TEST_URL}",),
    )

    result = await run_pipeline(url=TEST_URL)
    evidence = serialize_result(result)

    console.demo_step(
        "Observed Quote Evidence",
        "The browser flow returned bounding boxes and annotated image metadata.",
    )
    console.print_json(evidence)
    display_notebook_images(result)
    console.demo_outcome(
        "The quote concept returns public evidence values without exposing the "
        "Playwright page or locator objects.",
    )


if __name__ == "__main__":
    run_async(main())


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
{
  "element_quotes": [
    {
      "bbox_has_positive_size": true,
      "element_type": "picture",
      "found": true,
      "id": "P_2",
      "image_mode": "RGB",
      "image_size": [
        1280,
        1024
      ]
    },
    {
      "bbox_has_positive_size": true,
      "element_type": "table",
      "found": true,
      "id": "T_1",
      "image_mode": "RGB",
      "image_size": [
        1280,
        1024
      ]
    },
    {
      "bbox_has_positive_size": true,
      "element_type": "math",
      "found": true,
      "id": "M_0",
      "image_mode": "RGB",
      "image_size": [
        1280,
        1024
      ]
    }
  ],
  "text_quote": {
    "bbox_has_positive_size": true,
    "image_mode": "RGB",
    "image_size": [
      1280,
      1024
    ],
    "rect_count": 15,
    "text": "The theorem can be written as an equation relating the lengths..."
  }
}

Notebook output displays each annotated viewport screenshot directly, matching
the e2e demo style.
""".strip()
