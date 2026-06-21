# %%
"""Quote text and elements e2e: text edge cases.

Why:
    Verifies that the public text quote API handles representative copied text
    shapes such as links, emphasis, multi-line text, citations, and list items.

Covers:
    Area: quote text and elements
    Behavior: text lookup across common rendered-page edge cases
    Interface: `quote_text(...)`

Checks:
    If each representative text case is quoted, then the response contains at
    least one match with text, word boxes, and image metadata.
    If each response is serialized for review, then it matches the committed
    stable snapshot without storing raw image bytes.

Notes:
    Pytest uses the committed local fixture page. Manual demo runs use the live
    source page and should prove the same public workflow for every case.

Examples:
    Run manually:
        uv run python -m \
            tests.web_tools.e2e.quote_text_and_elements.test_quote_text_edge_cases

    Run as test:
        pytest tests/web_tools/e2e/quote_text_and_elements/test_quote_text_edge_cases.py
"""

from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True, slots=True)
class QuoteTextCase:
    """One representative public text quoting case."""

    case_id: str
    text: str


TEST_CASES = (
    QuoteTextCase(
        case_id="standard_text_with_links",
        text=(
            "The theorem can be written as an equation "
            "relating the lengths of the sides a, b and the hypotenuse c"
        ),
    ),
    QuoteTextCase(
        case_id="text_with_bold_formatting",
        text="sometimes called the Pythagorean equation",
    ),
    QuoteTextCase(
        case_id="multi_line_text",
        text=(
            "It states that the area of the square whose side is the hypotenuse "
            "(the side opposite the right angle) is equal to the sum of the areas "
            "of the squares on the other two sides."
        ),
    ),
    QuoteTextCase(
        case_id="text_with_adjacent_citations",
        text=(
            "The Plimpton 322 tablet records Pythagorean triples from Babylonian times."
        ),
    ),
    QuoteTextCase(
        case_id="short_unique_phrase",
        text="Gougu theorem",
    ),
    QuoteTextCase(
        case_id="text_in_list_item",
        text="The area of a triangle is half the area of any parallelogram",
    ),
)


# =============================================================================
# Helpers
# =============================================================================


def serialize_match(match: QuoteMatch) -> dict[str, object]:
    """Serialize one stable text-match evidence record."""
    return {
        "text": match.text,
        "bbox_count": len(match.boxes),
        "image_size": list(match.image.size),
        "image_mode": match.image.mode,
    }


def serialize_response(matches: list[QuoteMatch]) -> dict[str, object]:
    """Serialize stable public evidence for snapshot comparison."""
    return {
        "found": len(matches) > 0,
        "match_count": len(matches),
        "matches": [serialize_match(match) for match in matches],
    }


def _case_params() -> list[pytest.ParameterSet]:
    """Build named pytest params from stable case IDs."""
    return [pytest.param(case, id=case.case_id) for case in TEST_CASES]


# =============================================================================
# Pipeline
# =============================================================================


async def run_pipeline(*, case: QuoteTextCase, url: str) -> list[QuoteMatch]:
    """Run one public text edge-case quote flow."""
    return await quote_text(url=url, text=case.text)


# =============================================================================
# Assertions
# =============================================================================


def assert_quote_text_response(
    actual: dict[str, object],
    snapshot: SnapshotAssertion,
) -> None:
    """Assert the stable text edge-case quote evidence."""
    # First prove the caller-visible lookup returned at least one text match.
    assert actual["found"] is True
    assert actual["match_count"] > 0

    # Then compare only stable text, box-count, and image metadata.
    assert actual == snapshot


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _case_params())
async def test_quote_text_edge_cases(
    case: QuoteTextCase,
    snapshot: SnapshotAssertion,
    e2e_site_url: str,
) -> None:
    """Verify representative text quoting edge cases through the public API."""
    matches = await run_pipeline(case=case, url=e2e_site_url)
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
        "Finding every representative copied-text case on the live source page.",
        details=(f"URL: {TEST_URL}", f"case_count: {len(TEST_CASES)}"),
    )

    for index, case in enumerate(TEST_CASES, start=1):
        matches = await run_pipeline(case=case, url=TEST_URL)
        actual = serialize_response(matches)
        assert actual["found"] is True

        console.demo_step(
            f"Observed Case {index}: {case.case_id}",
            "The public response contains text-match screenshot evidence.",
            details=(f"match_count: {actual['match_count']}",),
        )
        if matches:
            display(matches[0].image)

    console.demo_outcome(
        "This proves `quote_text(...)` handles representative copied-text shapes.",
    )


if __name__ == "__main__":
    run_async(main())

# %%
