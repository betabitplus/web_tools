"""Package-specific pytest fixtures for `web_tools`.

Why:
    Keeps product cleanup under the package test tree while root pytest setup
    stays reusable across projects.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def clear_web_tools_caches_after_test() -> Generator[None]:
    """Clear cached config and resolver state after each `web_tools` test."""
    yield

    from web_tools._internal.config import (
        build_default_config,
        get_default_web_tools_resolver,
        install_web_tools_config,
    )

    install_web_tools_config(build_default_config())
    get_default_web_tools_resolver.cache_clear()
