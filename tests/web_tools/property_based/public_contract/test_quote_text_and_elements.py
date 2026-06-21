"""Quote public-contract properties.

Why:
    Protects generated public usage-error behavior for visual element IDs
    without launching browser-backed quote workflows.

Covers:
    Area: quote text and elements
    Behavior: invalid visual element ID usage errors
    Interface: `quote_element(...)` and `InvalidElementIdError`

Checks:
    If generated element IDs do not match public `P_N`, `T_N`, or `M_N`
    vocabulary, then `quote_element(...)` raises `InvalidElementIdError`.
"""

from __future__ import annotations

import re

import pytest
from hypothesis import given, settings, strategies as st
from py_lib_tooling import run_async

from web_tools import InvalidElementIdError, WebToolsError, quote_element

# =============================================================================
# Strategies
# =============================================================================

_PROPERTY_SETTINGS = settings(max_examples=40)

_VALID_ELEMENT_ID_PATTERN = re.compile(r"^[PTM]_(0|[1-9][0-9]*)$")
_INVALID_ELEMENT_ID = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-",
    min_size=0,
    max_size=12,
).filter(lambda value: _VALID_ELEMENT_ID_PATTERN.match(value) is None)


# =============================================================================
# Assertions
# =============================================================================


def assert_invalid_element_id_error(
    error: InvalidElementIdError,
    *,
    element_id: str,
) -> None:
    """Assert public invalid-element usage error attribution."""
    assert isinstance(error, WebToolsError)
    assert error.element_id == element_id
    assert element_id in str(error)


# =============================================================================
# Properties
# =============================================================================


@_PROPERTY_SETTINGS
@given(element_id=_INVALID_ELEMENT_ID)
def test_quote_element_rejects_generated_invalid_public_ids(element_id: str) -> None:
    """Generated invalid element IDs should fail at the public usage boundary."""
    with pytest.raises(InvalidElementIdError) as exc_info:
        run_async(quote_element(element_id, "https://example.com/"))

    assert_invalid_element_id_error(exc_info.value, element_id=element_id)
