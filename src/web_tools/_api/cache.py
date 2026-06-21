"""Public cache configuration facade.

Why:
    Shows the caller-facing cache setup function while path normalization and
    cache mechanics stay private.
"""

from __future__ import annotations

from pathlib import Path

from web_tools._internal import configure_page_cache_from_user_path

# ================================================================================
# Public API
# ================================================================================


def configure_cache(cache_dir: str | Path | None) -> None:
    """Configure page-artifact caching for public `web_tools` operations."""
    configure_page_cache_from_user_path(cache_dir)
