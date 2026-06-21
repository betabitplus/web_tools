# %%
"""Quote text and elements e2e: picture visual element.

Why:
    Verifies that the public visual-element quote API can locate a picture
    element and return screenshot evidence.

Covers:
    Area: quote text and elements
    Behavior: picture element lookup, bounding box evidence, annotated screenshot
    Interface: `quote_element(...)`

Checks:
    If the public element quote finds the picture target, then the response
    exposes the target ID, element type, bounding box shape, and image metadata.
    If the response is serialized for review, then it matches the committed
    stable snapshot without storing raw image bytes.

Notes:
    Pytest uses the committed local fixture page. Manual demo runs use the live
    source page and should prove the same public workflow.

Examples:
    Run manually:
        uv run python -m \
            tests.web_tools.e2e.quote_text_and_elements.test_quote_picture_pipeline

    Run as test:
        pytest \
            tests/web_tools/e2e/quote_text_and_elements/test_quote_picture_pipeline.py
"""

from __future__ import annotations

import pytest
from IPython.display import display
from py_lib_tooling import console, run_async
from syrupy.assertion import SnapshotAssertion

from web_tools import VisualElementMatch, quote_element

pytestmark = [
    pytest.mark.e2e_behavior,
    pytest.mark.e2e_contract,
    pytest.mark.hermetic,
]


# =============================================================================
# Scenario
# =============================================================================

TEST_URL = (
    "https://sankalp.bearblog.dev/"
    "my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/"
)
TARGET_ELEMENT_ID = "P_5"


# =============================================================================
# Helpers
# =============================================================================


def load_inputs(url: str = TEST_URL) -> dict[str, str]:
    """Load public inputs for the picture-element quote flow."""
    return {
        "element_id": TARGET_ELEMENT_ID,
        "url": url,
    }


def serialize_response(response: VisualElementMatch | None) -> dict[str, object]:
    """Serialize stable public evidence for snapshot comparison."""
    if response is None:
        return {
            "found": False,
            "id": TARGET_ELEMENT_ID,
        }

    return {
        "found": True,
        "id": response.id,
        "element_type": response.element_type,
        "bbox_keys": sorted(response.bbox.keys()),
        "bbox_has_positive_size": (
            response.bbox.get("width", 0) > 0 and response.bbox.get("height", 0) > 0
        ),
        "image_size": list(response.image.size),
        "image_mode": response.image.mode,
    }


# =============================================================================
# Pipeline
# =============================================================================


async def run_pipeline(*, element_id: str, url: str) -> VisualElementMatch | None:
    """Run the public picture-element quote flow."""
    return await quote_element(element_id, url)


# =============================================================================
# Assertions
# =============================================================================


def assert_visual_element_response(
    actual: dict[str, object],
    snapshot: SnapshotAssertion,
) -> None:
    """Assert the stable picture-element quote evidence."""
    # First prove the caller-visible lookup succeeded.
    assert actual["found"] is True
    assert actual["id"] == TARGET_ELEMENT_ID

    # Then keep volatile image data out while snapshotting stable evidence.
    assert actual["bbox_has_positive_size"] is True
    assert actual == snapshot


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
async def test_quote_picture_pipeline_hermetic(
    snapshot: SnapshotAssertion,
    e2e_site_url: str,
) -> None:
    """Verify picture visual-element quoting through the public API."""
    inputs = load_inputs(e2e_site_url)
    response = await run_pipeline(**inputs)
    actual = serialize_response(response)

    assert_visual_element_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


async def main() -> None:
    """Run the e2e scenario as a direct live manual check."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Finding one picture element on the live source page.",
        details=(f"URL: {TEST_URL}", f"target_element_id: {TARGET_ELEMENT_ID}"),
    )

    inputs = load_inputs()
    response = await run_pipeline(**inputs)
    actual = serialize_response(response)
    assert actual["found"] is True
    assert actual["bbox_has_positive_size"] is True

    console.demo_step(
        "Observed Element Evidence",
        "The public response contains a picture element and screenshot metadata.",
    )
    console.print_json(actual)
    if response is not None:
        display(response.image)
    console.demo_outcome(
        "This proves `quote_element(...)` can return picture-element evidence.",
    )


if __name__ == "__main__":
    run_async(main())

# %%
