# %%
"""Quote text and elements e2e: text normalization cases.

Why:
    Verifies that the public text quote API keeps useful copy/paste
    normalization while rejecting an ambiguous bare fraction case.

Covers:
    Area: quote text and elements
    Behavior: missing-space, dash, exponent, multiply, and fraction normalization
    Interface: `quote_text(...)`

Checks:
    If a normalization variant is supported, then the public quote response
    contains at least one match.
    If a normalization variant is ambiguous, then the public quote response
    returns no matches.

Notes:
    Pytest uses the committed local fixture page. Manual demo runs use the live
    source page and should prove the same public workflow for every case.

Examples:
    Run manually:
        uv run python -m \
            tests.web_tools.e2e.quote_text_and_elements.test_quote_text_normalization_cases

    Run as test:
        pytest \
            tests/web_tools/e2e/quote_text_and_elements/test_quote_text_normalization_cases.py
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from IPython.display import display
from py_lib_tooling import console, run_async

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
class TextNormalizationCase:
    """One public text-normalization expectation."""

    case_id: str
    text: str
    expected_found: bool


TEST_CASES = (
    TextNormalizationCase(
        case_id="missing_space_camelcase",
        text="The Arithmetical Classic of theGnomon and the Circular Paths of Heaven",
        expected_found=True,
    ),
    TextNormalizationCase(
        case_id="hyphen_vs_endash",
        text="c. 570 - c. 495 BC",
        expected_found=True,
    ),
    TextNormalizationCase(
        case_id="caret_exponent",
        text="a^2 + b^2 = c^2",
        expected_found=True,
    ),
    TextNormalizationCase(
        case_id="ascii_multiply",
        text="A x B2",
        expected_found=True,
    ),
    TextNormalizationCase(
        case_id="bare_fraction_ambiguous",
        text="1/2",
        expected_found=False,
    ),
)


# =============================================================================
# Helpers
# =============================================================================


def _case_params() -> list[pytest.ParameterSet]:
    """Build named pytest params from stable case IDs."""
    return [pytest.param(case, id=case.case_id) for case in TEST_CASES]


def format_case_result(
    *,
    case: TextNormalizationCase,
    matches: list[QuoteMatch],
) -> dict[str, object]:
    """Format one normalization result for manual output."""
    return {
        "case_id": case.case_id,
        "expected_found": case.expected_found,
        "found": len(matches) > 0,
        "match_count": len(matches),
    }


# =============================================================================
# Pipeline
# =============================================================================


async def run_pipeline(
    *,
    case: TextNormalizationCase,
    url: str,
) -> list[QuoteMatch]:
    """Run one public text-normalization quote flow."""
    return await quote_text(case.text, url)


# =============================================================================
# Assertions
# =============================================================================


def assert_normalization_response(
    *,
    case: TextNormalizationCase,
    matches: list[QuoteMatch],
) -> None:
    """Assert the public normalization outcome for one case."""
    # The boolean outcome is the public contract for these normalization cases.
    assert (len(matches) > 0) is case.expected_found


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _case_params())
async def test_quote_text_normalization_cases(
    case: TextNormalizationCase,
    e2e_site_url: str,
) -> None:
    """Verify text normalization behavior through the public API."""
    matches = await run_pipeline(case=case, url=e2e_site_url)

    assert_normalization_response(case=case, matches=matches)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


async def main() -> None:
    """Run the e2e scenario as a direct live manual check."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Checking every text-normalization case on the live source page.",
        details=(f"URL: {TEST_URL}", f"case_count: {len(TEST_CASES)}"),
    )

    for index, case in enumerate(TEST_CASES, start=1):
        matches = await run_pipeline(case=case, url=TEST_URL)
        assert_normalization_response(case=case, matches=matches)

        result = format_case_result(case=case, matches=matches)
        console.demo_step(
            f"Observed Case {index}: {case.case_id}",
            "The public response matched the expected normalization outcome.",
        )
        console.print_json(result)
        if matches:
            display(matches[0].image)

    console.demo_outcome(
        "This proves `quote_text(...)` keeps useful normalization without "
        "over-matching ambiguous copied text.",
    )


if __name__ == "__main__":
    run_async(main())

# %%
