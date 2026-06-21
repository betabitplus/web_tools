# %%
"""Public output and errors e2e.

Why:
    Verifies that completed workflows and stopped workflows cross the package
    boundary as public DTOs, values, vocabulary, or public errors.

Covers:
    Area: public output and errors
    Behavior: terminal public outputs and attributable public usage errors
    Interface: top-level `web_tools` package exports

Checks:
    If public fetch and conversion workflows succeed, then callers receive
    `FetchResponse`, `str`, and `ConversionResponse` values.
    If public media policy prevents downloads, then callers receive an empty
    collection and public stats rather than private transport details.
    If caller input is invalid, then public `WebToolsError` subclasses carry
    attributable configuration or quote usage details.

Examples:
    Run manually:
        uv run python -m \
            tests.web_tools.e2e.public_output_and_errors.test_public_boundary_contracts

    Run as test:
        pytest \
            tests/web_tools/e2e/public_output_and_errors/test_public_boundary_contracts.py
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from py_lib_tooling import console, run_async

from web_tools import (
    ConversionResponse,
    FetchResponse,
    InvalidConfigValueError,
    InvalidElementIdError,
    MediaConfig,
    MediaDownloader,
    MediaType,
    VisualElementManifest,
    VisualElementType,
    WebToolsError,
    configure_cache,
    fetch_html,
    html2html,
    html2md,
    quote_element,
)

pytestmark = [
    pytest.mark.e2e_behavior,
    pytest.mark.e2e_contract,
    pytest.mark.hermetic,
]


# =============================================================================
# Scenario
# =============================================================================

TEST_URL = "https://example.com/"
INVALID_MEDIA_TYPE = "audio"
INVALID_ELEMENT_ID = "not-a-public-element-id"


# =============================================================================
# Helpers
# =============================================================================


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves boundary fixtures without request logs."""

    def log_message(self, format_string: str, *args: object) -> None:
        """Suppress per-request access logs during manual runs."""
        _ = format_string, args


@contextmanager
def serve_fixture_site() -> Iterator[str]:
    """Serve the committed e2e fixture site for manual execution."""
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "site"
    handler = partial(_QuietStaticHandler, directory=str(fixture_root))

    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/index.html"
        finally:
            server.shutdown()
            thread.join(timeout=5)


def media_url(site_url: str) -> str:
    """Build a loopback media URL from the shared e2e site URL."""
    site_root = site_url.rsplit("/", maxsplit=1)[0]
    return f"{site_root}/assets/media-image.png"


def serialize_error(error: WebToolsError) -> dict[str, object]:
    """Serialize public error evidence."""
    return {
        "type": type(error).__name__,
        "is_web_tools_error": isinstance(error, WebToolsError),
        "message": str(error),
    }


# =============================================================================
# Pipeline
# =============================================================================


async def run_success_outputs(*, url: str) -> dict[str, object]:
    """Run representative public success outputs."""
    configure_cache(None)
    try:
        fetch_response = await fetch_html(url, no_cache=True)
        readable_html = html2html(fetch_response.html, base_url=fetch_response.url)
        conversion_response = html2md(fetch_response.html, base_url=fetch_response.url)
    finally:
        configure_cache(None)

    with MediaDownloader(
        config=MediaConfig(enabled=False), cache_dir=None
    ) as downloader:
        media_items = downloader.download_from_post({"url": media_url(url)})
        media_stats = downloader.stats()

    return {
        "fetch_is_public_response": isinstance(fetch_response, FetchResponse),
        "fetch_has_html": bool(fetch_response.html.strip()),
        "readable_html_is_str": isinstance(readable_html, str),
        "readable_html_has_article": "Pythagorean theorem replay page" in readable_html,
        "conversion_is_public_response": isinstance(
            conversion_response,
            ConversionResponse,
        ),
        "manifest_is_public_response": isinstance(
            conversion_response.manifest,
            VisualElementManifest,
        ),
        "manifest_counts": conversion_response.manifest.counts,
        "first_manifest_type": conversion_response.manifest.elements[0].element_type,
        "media_item_count": len(media_items),
        "media_stats_enabled": media_stats["enabled"],
    }


async def run_error_outputs() -> dict[str, dict[str, object]]:
    """Run representative public error outputs."""
    try:
        MediaConfig(allowed_types=[INVALID_MEDIA_TYPE])
    except InvalidConfigValueError as error:
        media_config_error = serialize_error(error)
    else:
        msg = "Expected InvalidConfigValueError for unsupported media type."
        raise AssertionError(msg)

    try:
        await quote_element(INVALID_ELEMENT_ID, TEST_URL)
    except InvalidElementIdError as error:
        quote_error = serialize_error(error)
    else:
        msg = "Expected InvalidElementIdError for invalid visual element ID."
        raise AssertionError(msg)

    return {
        "media_config": media_config_error,
        "quote_element": quote_error,
    }


# =============================================================================
# Assertions
# =============================================================================


def assert_success_outputs(result: dict[str, object]) -> None:
    """Assert representative public success outputs."""
    # Completed page workflows return public DTOs and public values.
    assert result["fetch_is_public_response"] is True
    assert result["fetch_has_html"] is True
    assert result["readable_html_is_str"] is True
    assert result["readable_html_has_article"] is True
    assert result["conversion_is_public_response"] is True
    assert result["manifest_is_public_response"] is True

    # Visual and media categories stay in public vocabulary.
    assert result["manifest_counts"] == {
        "total": 8,
        "picture": 7,
        "table": 1,
        "math": 0,
    }
    assert result["first_manifest_type"] == VisualElementType.PICTURE
    assert MediaType.IMAGE.value == "image"

    # Disabled media policy returns public empty output and stats.
    assert result["media_item_count"] == 0
    assert result["media_stats_enabled"] is False


def assert_error_outputs(result: dict[str, dict[str, object]]) -> None:
    """Assert representative public error outputs."""
    assert result["media_config"]["type"] == "InvalidConfigValueError"
    assert result["media_config"]["is_web_tools_error"] is True
    assert INVALID_MEDIA_TYPE in str(result["media_config"]["message"])

    assert result["quote_element"]["type"] == "InvalidElementIdError"
    assert result["quote_element"]["is_web_tools_error"] is True
    assert INVALID_ELEMENT_ID in str(result["quote_element"]["message"])


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
async def test_public_success_outputs_are_boundary_values(
    e2e_site_url: str,
) -> None:
    """Verify successful workflows return public boundary values."""
    result = await run_success_outputs(url=e2e_site_url)

    assert_success_outputs(result)


@pytest.mark.asyncio
async def test_public_errors_are_boundary_errors() -> None:
    """Verify stopped workflows return public error types."""
    result = await run_error_outputs()

    assert_error_outputs(result)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


async def main() -> None:
    """Run the e2e scenario as a direct live manual check."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Serving committed page fixtures over loopback and checking boundary "
        "outputs plus public usage errors.",
        details=(f"fallback_demo_url: {TEST_URL}",),
    )

    with serve_fixture_site() as site_url:
        success = await run_success_outputs(url=site_url)
    errors = await run_error_outputs()

    assert_success_outputs(success)
    assert_error_outputs(errors)

    console.demo_step(
        "Observed Boundary Outputs",
        "The public package returned stable DTOs, values, vocabulary, empty "
        "media output, and named public errors.",
    )
    console.print_json({"success": success, "errors": errors})
    console.demo_outcome(
        "This proves callers can understand success and stopped workflows "
        "without reading private runtime code.",
    )


if __name__ == "__main__":
    run_async(main())

# %%
