"""Public config snapshot property tests.

Why:
    Protects the public config contract with property-based routing in the same
    tree shape used by mature py libraries.
"""

from __future__ import annotations

from hypothesis import given, strategies as st

from web_tools import WebToolsConfig, get_web_tools_config

# =============================================================================
# Properties
# =============================================================================


@given(st.none())
def test_explicit_config_snapshot_round_trips(value: None) -> None:
    """Hypothesis inputs do not change explicit config snapshot identity."""
    _ = value
    config = WebToolsConfig()

    assert get_web_tools_config(config) is config
