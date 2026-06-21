"""Validation and parsing helpers for quoting."""

from __future__ import annotations

import re

from web_tools._api.errors import InvalidElementIdError
from web_tools._api.types import VisualElementType

_ELEMENT_ID_PATTERN = re.compile(r"^(?P<prefix>[PTM])_(?P<index>0|[1-9][0-9]*)$")


def parse_element_id(element_id: str) -> tuple[VisualElementType, str, int]:
    """Parse element ID into (element_type, selector, index)."""
    match = _ELEMENT_ID_PATTERN.match(element_id)
    if match is None:
        raise InvalidElementIdError(element_id=element_id)

    prefix = match.group("prefix")
    index = int(match.group("index"))
    if prefix == "P":
        return (VisualElementType.PICTURE, "img", index)
    if prefix == "T":
        return (VisualElementType.TABLE, "table", index)
    if prefix == "M":
        # Math formulas on Wikipedia are images with class mwe-math-fallback-image-*
        # Match both display and inline math images.
        return (
            VisualElementType.MATH,
            "img[class*='mwe-math-fallback-image']",
            index,
        )

    raise InvalidElementIdError(element_id=element_id)
