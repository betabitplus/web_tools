"""Fetch cache public-contract properties.

Why:
    Protects generated invariants for public fetch response values without
    depending on browser or network execution.

Covers:
    Area: fetch cache and page artifacts
    Behavior: caller-visible fetched HTML, final URL, metadata, cache evidence
    Interface: `FetchResponse`

Checks:
    If callers receive generated fetch response values, then those values stay
    visible through public fields unchanged.
    If cache evidence is generated as true or false, then `FetchResponse`
    preserves that public cache decision.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

from web_tools import FetchResponse

# =============================================================================
# Strategies
# =============================================================================

_PROPERTY_SETTINGS = settings(max_examples=40)

_SAFE_TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_",
    min_size=1,
    max_size=40,
)
_URL = st.from_regex(
    r"https://example\.com/[a-z0-9][a-z0-9/_-]{0,24}",
    fullmatch=True,
)
_METADATA = st.dictionaries(
    keys=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz_",
        min_size=1,
        max_size=12,
    ),
    values=st.one_of(
        st.booleans(), st.integers(min_value=0, max_value=100), _SAFE_TEXT
    ),
    max_size=4,
)


# =============================================================================
# Assertions
# =============================================================================


def assert_fetch_response_preserves_public_values(
    response: FetchResponse,
    *,
    html: str,
    url: str,
    from_cache: bool,
    metadata: dict[str, object],
) -> None:
    """Assert public fetch response field preservation."""
    # The caller-visible artifact is the HTML string and final URL.
    assert response.html == html
    assert response.url == url

    # Cache evidence and metadata should cross as public values, not as
    # implementation-specific cache entries.
    assert response.from_cache is from_cache
    assert response.metadata == metadata


# =============================================================================
# Properties
# =============================================================================


@_PROPERTY_SETTINGS
@given(
    html=_SAFE_TEXT,
    url=_URL,
    from_cache=st.booleans(),
    metadata=_METADATA,
)
def test_fetch_response_preserves_public_cache_evidence(
    *,
    html: str,
    url: str,
    from_cache: bool,
    metadata: dict[str, object],
) -> None:
    """Generated fetch responses should preserve public artifact evidence."""
    response = FetchResponse(
        html=html,
        url=url,
        from_cache=from_cache,
        metadata=metadata,
    )

    assert_fetch_response_preserves_public_values(
        response,
        html=html,
        url=url,
        from_cache=from_cache,
        metadata=metadata,
    )
