# %%
"""Workbench scenario: fetch cache and page artifacts.

Why:
    Isolates the page-artifact cache behavior behind the fetch concept without
    importing shipped `web_tools` code.

Covers:
    Area: fetch cache and page artifacts
    Behavior: live URL retrieval, cache hit evidence, force refresh, no-cache fetch
    Interface: `httpx.get(...)` plus `diskcache.Cache`

Checks:
    If a page URL is fetched with an empty cache, then the returned artifact is
    fresh and contains HTML.
    If the same page URL is fetched again with the same cache, then the
    returned artifact is marked as coming from cache.
    If force refresh or no-cache is requested, then the returned artifact is
    fresh instead of reusing the cached value.

Examples:
    Run manually:
        uv run python -m workbench.web_tools.fetch_cache_and_page_artifacts
        uv run py-lib-reproduce-running-loop \
            workbench.web_tools.fetch_cache_and_page_artifacts
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast
from urllib.parse import urlparse

import httpx
from diskcache import Cache
from py_lib_tooling import console

# =============================================================================
# Scenario
# =============================================================================

TEST_URL = "https://example.com/"


@dataclass(frozen=True, slots=True)
class PageArtifact:
    """Caller-visible page artifact used by this isolated probe."""

    html: str
    url: str
    from_cache: bool
    metadata: dict[str, str]


# =============================================================================
# Helpers
# =============================================================================


def _cache_key(url: str) -> str:
    """Return a stable URL cache key without exposing storage layout."""
    digest = hashlib.sha256(url.encode(), usedforsecurity=False).hexdigest()
    return f"page:{digest}"


def _read_http_url(url: str) -> PageArtifact:
    """Read a live HTTP page when the scenario URL is external."""
    response = httpx.get(url, follow_redirects=True, timeout=10)
    response.raise_for_status()
    return PageArtifact(
        html=response.text,
        url=str(response.url),
        from_cache=False,
        metadata={"source": "http", "status_code": str(response.status_code)},
    )


def _read_uncached_page(url: str) -> PageArtifact:
    """Fetch one page artifact without consulting the cache."""
    scheme = urlparse(url).scheme
    if scheme in {"http", "https"}:
        return _read_http_url(url)

    msg = f"Unsupported page URL scheme: {scheme!r}."
    raise ValueError(msg)


def _serialize_artifact(artifact: PageArtifact) -> dict[str, Any]:
    """Serialize stable fetch evidence for manual output."""
    return {
        "from_cache": artifact.from_cache,
        "html_length": len(artifact.html),
        "has_example_domain": "Example Domain" in artifact.html,
        "source": artifact.metadata["source"],
        "url_scheme": urlparse(artifact.url).scheme,
    }


# =============================================================================
# Pipeline
# =============================================================================


def fetch_page_artifact(
    url: str,
    *,
    cache_dir: Path,
    force_refresh: bool = False,
    no_cache: bool = False,
) -> PageArtifact:
    """Fetch one page artifact through the isolated cache policy."""
    if no_cache:
        return _read_uncached_page(url)

    with Cache(str(cache_dir)) as cache:
        key = _cache_key(url)
        cached_entry = cache.get(key, default=None)
        if not force_refresh and isinstance(cached_entry, dict):
            cached = cast("dict[str, Any]", cached_entry)
            return PageArtifact(
                html=str(cached["html"]),
                url=str(cached["url"]),
                from_cache=True,
                metadata=cast("dict[str, str]", cached["metadata"]),
            )

        artifact = _read_uncached_page(url)
        cache[key] = {
            "html": artifact.html,
            "url": artifact.url,
            "metadata": artifact.metadata,
        }
        return artifact


def run_pipeline(*, url: str, cache_dir: Path) -> dict[str, object]:
    """Run the isolated fetch/cache concept flow."""
    first = fetch_page_artifact(url, cache_dir=cache_dir)
    second = fetch_page_artifact(url, cache_dir=cache_dir)
    refreshed = fetch_page_artifact(url, cache_dir=cache_dir, force_refresh=True)
    uncached = fetch_page_artifact(url, cache_dir=cache_dir, no_cache=True)

    return {
        "same_url": first.url == second.url == refreshed.url == uncached.url,
        "artifacts": {
            "first": _serialize_artifact(first),
            "second": _serialize_artifact(second),
            "force_refresh": _serialize_artifact(refreshed),
            "no_cache": _serialize_artifact(uncached),
        },
    }


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the workbench script as a narrative manual demo."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Fetching one live HTTP page through an isolated cache policy.",
        details=(f"url: {TEST_URL}",),
    )

    with TemporaryDirectory() as temp_dir:
        evidence = run_pipeline(url=TEST_URL, cache_dir=Path(temp_dir))

    console.demo_step(
        "Observed Cache Evidence",
        "The second fetch reused the page artifact while explicit bypasses "
        "returned fresh artifacts.",
    )
    console.print_json(evidence)
    console.demo_outcome(
        "The page artifact carries caller-visible cache evidence without "
        "depending on shipped package internals.",
    )


if __name__ == "__main__":
    main()


# =============================================================================
# Expected Output
# =============================================================================
EXPECTED_OUTPUT = """
{
  "artifacts": {
    "first": {
      "from_cache": false,
      "has_example_domain": true,
      "html_length": 528,
      "source": "http",
      "url_scheme": "https"
    },
    "force_refresh": {
      "from_cache": false,
      "has_example_domain": true,
      "html_length": 528,
      "source": "http",
      "url_scheme": "https"
    },
    "no_cache": {
      "from_cache": false,
      "has_example_domain": true,
      "html_length": 528,
      "source": "http",
      "url_scheme": "https"
    },
    "second": {
      "from_cache": true,
      "has_example_domain": true,
      "html_length": 528,
      "source": "http",
      "url_scheme": "https"
    }
  },
  "same_url": true
}
""".strip()
