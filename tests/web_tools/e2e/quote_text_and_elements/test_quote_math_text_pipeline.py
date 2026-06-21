# %%
r"""Quote text and elements e2e: math text.

Why:
    Verifies that the public text quote API can locate markdown-style math text
    and return screenshot evidence for the match.

Covers:
    Area: quote text and elements
    Behavior: math text lookup, match boxes, annotated screenshot
    Interface: `quote_text(...)`

Checks:
    If the public text quote finds the math text, then the response contains at
    least one match with text, word boxes, and image metadata.
    If the response is serialized for review, then it matches the committed
    stable snapshot without storing raw image bytes.

Notes:
    Pytest uses the committed local fixture page. Manual demo runs use the live
    source page and should prove the same public workflow.

Examples:
    Run manually:
        uv run python -m \
            tests.web_tools.e2e.quote_text_and_elements.test_quote_math_text_pipeline

    Run as test:
        pytest \
            tests/web_tools/e2e/quote_text_and_elements/test_quote_math_text_pipeline.py
"""

from __future__ import annotations

import pytest
from IPython.display import display
from py_lib_tooling import console, run_async
from syrupy.assertion import SnapshotAssertion

from web_tools import QuoteMatch, quote_text

pytestmark = [
    pytest.mark.e2e_behavior,
    pytest.mark.e2e_contract,
    pytest.mark.hermetic,
]


# =============================================================================
# Scenario
# =============================================================================

TEST_URL = "https://en.wikipedia.org/wiki/Pythagorean_theorem"
TARGET_TEXT = r"And likewise, at all moments in time, the area is always _a_ 2 \+ _b_ 2"


# =============================================================================
# Helpers
# =============================================================================


def load_inputs(url: str = TEST_URL) -> dict[str, str]:
    """Load public inputs for the math-text quote flow."""
    return {
        "text": TARGET_TEXT,
        "url": url,
    }


def serialize_response(matches: list[QuoteMatch]) -> dict[str, object]:
    """Serialize stable public evidence for snapshot comparison."""
    return {
        "found": len(matches) > 0,
        "match_count": len(matches),
        "matches": [
            {
                "text": match.text,
                "bbox_count": len(match.boxes),
                "image_size": list(match.image.size),
                "image_mode": match.image.mode,
            }
            for match in matches
        ],
    }


# =============================================================================
# Pipeline
# =============================================================================


async def run_pipeline(*, text: str, url: str) -> list[QuoteMatch]:
    """Run the public math-text quote flow."""
    return await quote_text(text, url)


# =============================================================================
# Assertions
# =============================================================================


def assert_quote_text_response(
    actual: dict[str, object],
    snapshot: SnapshotAssertion,
) -> None:
    """Assert the stable math-text quote evidence."""
    # First prove the caller-visible lookup returned at least one text match.
    assert actual["found"] is True
    assert actual["match_count"] > 0

    # Then compare only stable text, box-count, and image metadata.
    assert actual == snapshot


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
async def test_quote_math_text_pipeline_hermetic(
    snapshot: SnapshotAssertion,
    e2e_site_url: str,
) -> None:
    """Verify math text quoting through the public API."""
    inputs = load_inputs(e2e_site_url)
    matches = await run_pipeline(**inputs)
    actual = serialize_response(matches)

    assert_quote_text_response(actual, snapshot)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


async def main() -> None:
    """Run the e2e scenario as a direct live manual check."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Finding one markdown-style math text span on the live source page.",
        details=(f"URL: {TEST_URL}", f"target_text: {TARGET_TEXT}"),
    )

    inputs = load_inputs()
    matches = await run_pipeline(**inputs)
    actual = serialize_response(matches)
    assert actual["found"] is True

    console.demo_step(
        "Observed Text Evidence",
        "The public response contains text matches and screenshot metadata.",
    )
    console.print_json(actual)
    if matches:
        display(matches[0].image)
    console.demo_outcome(
        "This proves `quote_text(...)` can return math-text evidence.",
    )


if __name__ == "__main__":
    run_async(main())

# %%
