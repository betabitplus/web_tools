"""Declaration and facade layer for the `web_tools` public surface.

Why:
    Keeps stable caller-facing shapes in one place while fetching, conversion,
    browser automation, cache, and media-download machinery stays private.

What belongs here:
    Public DTOs, vocabulary enums, config objects, exception types, and thin
    facade functions/classes that are re-exported by `web_tools`.

What does not belong here:
    Browser orchestration, HTTP/cache mechanics, provider workarounds, parsing
    pipelines, or logging/config loader infrastructure.

Notes:
    Callers should import from the top-level `web_tools` package. This `_api`
    package exists to organize and document the supported surface, not to
    become a second user-facing import style.
"""
