"""Private screenshot annotation helpers for quote evidence."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class PageElement:
    """A normalized page element bounding box with a label."""

    content: str
    coord: list[float]


@dataclass(frozen=True)
class AnnotationResponse:
    """Annotated image response."""

    response_data: Image.Image
    metadata: dict[str, object]


def _absolute_box(
    coord: list[float],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    """Convert normalized coordinates to an absolute pixel box."""
    x0, y0, x1, y1 = coord
    return (
        max(0, min(width, int(x0 * width))),
        max(0, min(height, int(y0 * height))),
        max(0, min(width, int(x1 * width))),
        max(0, min(height, int(y1 * height))),
    )


def annotate(image: Image.Image, elements: list[PageElement]) -> AnnotationResponse:
    """Draw page-element boxes and labels on a copy of an image."""
    annotated = image.copy().convert("RGB")
    draw = ImageDraw.Draw(annotated)
    font = ImageFont.load_default()

    for element in elements:
        box = _absolute_box(element.coord, annotated.width, annotated.height)
        draw.rectangle(box, outline=(255, 0, 0), width=3)
        label_origin = (box[0], max(0, box[1] - 12))
        draw.text(label_origin, element.content, fill=(255, 0, 0), font=font)

    return AnnotationResponse(
        response_data=annotated,
        metadata={"element_count": len(elements)},
    )
