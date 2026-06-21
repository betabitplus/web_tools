# %%
"""Web tools public config boundary scenario.

Why:
    Verifies that the top-level package API can install and read a runtime
    config snapshot end to end.
"""

from __future__ import annotations

import pytest
from py_lib_tooling import console

from web_tools import WebToolsConfig, get_web_tools_config, install_web_tools_config

pytestmark = [
    pytest.mark.e2e_contract,
    pytest.mark.hermetic,
]

# =============================================================================
# Pipeline
# =============================================================================


def run_pipeline() -> WebToolsConfig:
    """Run the public config install/read flow."""
    return install_web_tools_config(WebToolsConfig())


# =============================================================================
# Assertions
# =============================================================================


def assert_public_config_response(config: WebToolsConfig) -> None:
    """Assert the public config snapshot is the installed runtime snapshot."""
    assert get_web_tools_config() is config


# =============================================================================
# Tests
# =============================================================================


def test_public_config_pipeline() -> None:
    """The public config lifecycle works through the top-level package."""
    config = run_pipeline()

    assert_public_config_response(config)


# =============================================================================
# Demo (Manual Execution)
# =============================================================================


def main() -> None:
    """Run the public config boundary scenario as a manual demo."""
    console.demo_intro(__doc__)
    console.demo_step(
        "Scenario",
        "Installing a config snapshot through the public package.",
    )

    config = run_pipeline()
    assert_public_config_response(config)
    console.demo_step(
        "Observed Config",
        "The installed config is the active public runtime snapshot.",
        details=(f"config_type: {type(config).__name__}",),
    )
    console.demo_outcome("The public config boundary is wired correctly.")


if __name__ == "__main__":
    main()

# %%
