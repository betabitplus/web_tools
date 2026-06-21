"""Visual element annotation for Markdown documents."""

from __future__ import annotations

import re

from web_tools._api.types import VisualElement, VisualElementManifest, VisualElementType


def _is_table_start(lines: list[str], index: int) -> bool:
    """Return true if the current line begins a Markdown table."""
    if "|" not in lines[index]:
        return False
    if index + 1 >= len(lines):
        return False
    return re.match(r"^\s*\|?[\s\-:|]+\|", lines[index + 1]) is not None


def _consume_table(
    lines: list[str],
    start_index: int,
    table_index: int,
    result_lines: list[str],
    elements: list[VisualElement],
) -> int:
    """Consume a table block and append annotated markup + manifest element."""
    result_lines.append(f'<table id="T_{table_index}">')
    table_start = start_index
    current_index = start_index

    while current_index < len(lines) and "|" in lines[current_index]:
        result_lines.append(lines[current_index])
        current_index += 1

    row_count = current_index - table_start
    result_lines.append("</table>")

    elements.append(
        VisualElement(
            id=f"T_{table_index}",
            element_type=VisualElementType.TABLE,
            index=table_index,
            row_count=row_count,
        )
    )
    return current_index


def _is_math_image(alt_text: str | None) -> bool:
    """Return true if an image alt-text looks like a LaTeX render."""
    return bool(
        alt_text
        and alt_text.startswith(
            (
                r"{\\displaystyle",
                "{displaystyle",
            )
        )
    )


def _annotate_image_line(
    line: str,
    img_pattern: re.Pattern[str],
    picture_index: int,
    math_index: int,
    elements: list[VisualElement],
) -> tuple[str, int, int, bool]:
    """Wrap image markdown with <picture>/<math> tags and update indices."""
    img_matches = list(img_pattern.finditer(line))
    if not img_matches:
        return line, picture_index, math_index, False

    annotated_line = line
    for match in reversed(img_matches):
        full_match = match.group(1)
        alt_text = match.group(2) or None
        src_url = match.group(3)

        if _is_math_image(alt_text):
            elements.append(
                VisualElement(
                    id=f"M_{math_index}",
                    element_type=VisualElementType.MATH,
                    index=math_index,
                    src=src_url,
                    alt=alt_text,
                    latex=alt_text,
                )
            )
            wrapped = f'<math id="M_{math_index}">\n{full_match}\n</math>'
            math_index += 1
        else:
            elements.append(
                VisualElement(
                    id=f"P_{picture_index}",
                    element_type=VisualElementType.PICTURE,
                    index=picture_index,
                    src=src_url,
                    alt=alt_text,
                )
            )
            wrapped = f'<picture id="P_{picture_index}">\n{full_match}\n</picture>'
            picture_index += 1

        annotated_line = (
            annotated_line[: match.start()] + wrapped + annotated_line[match.end() :]
        )

    return annotated_line, picture_index, math_index, True


def annotate_visual_elements(markdown: str) -> tuple[str, VisualElementManifest]:
    """Annotate pictures/tables/math in Markdown and build a manifest."""
    lines = markdown.split("\n")
    result_lines: list[str] = []
    elements: list[VisualElement] = []

    picture_index = 0
    table_index = 0
    math_index = 0

    img_pattern = re.compile(r'(!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\))')

    in_code_block = False
    code_fence_pattern = re.compile(r"^(`{3,}|~{3,})")

    i = 0
    while i < len(lines):
        line = lines[i]

        if code_fence_pattern.match(line.strip()):
            in_code_block = not in_code_block
            result_lines.append(line)
            i += 1
            continue

        if in_code_block:
            result_lines.append(line)
            i += 1
            continue

        if _is_table_start(lines, i):
            i = _consume_table(lines, i, table_index, result_lines, elements)
            table_index += 1
            continue

        annotated_line, picture_index, math_index, did_annotate = _annotate_image_line(
            line,
            img_pattern,
            picture_index,
            math_index,
            elements,
        )
        result_lines.append(annotated_line if did_annotate else line)
        i += 1

    elements.sort(key=lambda element: (element.element_type.value, element.index))
    return "\n".join(result_lines), VisualElementManifest(elements=elements)
