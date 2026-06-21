"""Public package boundary unit tests.

Why:
    Protects supported top-level imports, config helpers, public errors, and
    package version metadata.
"""

from __future__ import annotations

import web_tools
from web_tools import InvalidConfigValueError, WebToolsConfig, WebToolsError

# =============================================================================
# Tests
# =============================================================================


def test_public_exports_resolve() -> None:
    """All supported public names are exported by the top-level package."""
    for name in web_tools.__all__:
        assert hasattr(web_tools, name)


def test_public_exception_is_package_specific() -> None:
    """The package exposes one public exception base."""
    assert issubclass(WebToolsError, Exception)


def test_public_config_exports_resolve() -> None:
    """The package exposes the shared config lifecycle."""
    installed = web_tools.install_web_tools_config(WebToolsConfig())

    assert web_tools.get_web_tools_config().__class__ is WebToolsConfig
    assert installed.__class__ is WebToolsConfig


def test_invalid_config_error_is_public() -> None:
    """The package exposes a config-specific public error."""
    error = InvalidConfigValueError(
        field="field",
        value={"secret": "redacted"},
        reason="bad",
    )

    assert isinstance(error, WebToolsError)
    assert "Invalid config value for" in str(error)


def test_version_is_available() -> None:
    """The package exposes distribution metadata."""
    assert web_tools.__version__
