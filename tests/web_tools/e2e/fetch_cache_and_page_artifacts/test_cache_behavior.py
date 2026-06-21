# %%
"""Fetch cache behavior e2e.

Why:
    Verifies that the public fetch facade returns explicit cache evidence when
    page-artifact caching is configured.

Covers:
    Area: fetch cache and page artifacts
    Behavior: cache configuration, repeated fetches, public cache evidence
    Interface: `configure_cache(...)` and `fetch_html(...)`

Checks:
    If the first public fetch uses an empty cache, then the response is not
    marked as coming from cache.
    If the same URL is fetched again with the same cache configured, then the
    second response is marked as coming from cache.

Examples:
    Run manually:
        uv run python -m \
            tests.web_tools.e2e.fetch_cache_and_page_artifacts.test_cache_behavior

    Run as test:
        pytest tests/web_tools/e2e/fetch_cache_and_page_artifacts/test_cache_behavior.py
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from py_lib_tooling import console, run_async

from web_tools import FetchResponse, configure_cache, fetch_html

pytestmark = [
    pytest.mark.e2e_behavior,
    pytest.mark.e2e_contract,
    pytest.mark.hermetic,
]


# =============================================================================
# Scenario
# =============================================================================

TEST_URL = "https://example.com/"


# =============================================================================
# Helpers
# =============================================================================


def serialize_response_pair(
    first_response: FetchResponse,
    second_response: FetchResponse,
) -> dict[str, object]:
    """Format cache evidence for assertions and manual output."""
    return {
        "first_from_cache": first_response.from_cache,
        "second_from_cache": second_response.from_cache,
        "first_has_html": bool(first_response.html.strip()),
        "second_has_html": bool(second_response.html.strip()),
        "same_url": first_response.url == second_response.url,
    }


# =============================================================================
# Pipeline
# =============================================================================


async def run_pipeline(*, cache_dir: Path, url: str) -> dict[str, object]:
    """Run the public cache-aware fetch flow."""
    configure_cache(cache_dir)
    try:
        first_response = await fetch_html(url)
        second_response = await fetch_html(url)
    finally:
        configure_cache(None)

    return serialize_response_pair(first_response, second_response)


# =============================================================================
# Assertions
# =============================================================================


def assert_cache_evidence(result: dict[str, object]) -> None:
    """Assert the public cache evidence for the scenario."""
    # First prove both public fetch calls returned page content.
    assert result["first_has_html"] is True
    assert result["second_has_html"] is True

    # Then prove the public cache signal changes across repeated fetches.
    assert result["first_from_cache"] is False
    assert result["second_from_cache"] is True
    assert result["same_url"] is True


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
async def test_fetch_html_cache_hit(tmp_path: Path, e2e_site_url: str) -> None:
    """Verify repeated public fetches expose cache hits."""
    result = await run_pipeline(
        cache_dir=tmp_path / "web_tools_cache",
        url=e2e_site_url,
    )

    assert_cache_evidence(result)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


async def main() -> None:
    """Run the e2e scenario as a direct live manual check."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Fetching one URL twice with the same configured cache.",
        details=(f"URL: {TEST_URL}",),
    )

    with TemporaryDirectory() as temp_dir:
        result = await run_pipeline(cache_dir=Path(temp_dir), url=TEST_URL)

    assert_cache_evidence(result)
    console.demo_step(
        "Observed Cache Evidence",
        "The second public fetch reported a cache hit.",
        details=(
            f"first_from_cache: {result['first_from_cache']}",
            f"second_from_cache: {result['second_from_cache']}",
        ),
    )
    console.print_json(result)
    console.demo_outcome(
        "This proves cache configuration reaches the public fetch workflow and "
        "`FetchResponse.from_cache` exposes the cache decision.",
    )


if __name__ == "__main__":
    run_async(main())

# %%
