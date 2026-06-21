"""Capture and annotation helpers for quoting."""

from __future__ import annotations

import io

from PIL import Image
from playwright.async_api import Page

from web_tools._api.types import VisualElementMatch, VisualElementType
from web_tools._internal.quote_manager.annotation import PageElement, annotate


def convert_js_boxes_to_page_elements(
    boxes: list[dict],
    img_width: int,
    img_height: int,
) -> list[PageElement]:
    """Convert JS bounding boxes (pixel coords) to normalized PageElement coords."""
    elements = []
    for i, box in enumerate(boxes):
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]
        coord = [
            float(x) / img_width,
            float(y) / img_height,
            float(x + w) / img_width,
            float(y + h) / img_height,
        ]
        elements.append(PageElement(content=f"match_{i + 1}", coord=coord))
    return elements


async def find_next_match(page: Page, text: str) -> bool:
    """Find/select the next occurrence of text on the page."""
    return await page.evaluate(
        """
        (text) => {
            if (window.find(text, false, false, false, false, false, false)) {
                return true;
            }

            const existingSelection = window.getSelection();
            if (
                existingSelection &&
                existingSelection.rangeCount > 0 &&
                existingSelection.toString()
            ) {
                return false;
            }

            const state = window.__webToolsFindState || { text: null, index: 0 };
            if (state.text !== text) {
                state.text = text;
                state.index = 0;
            }

            const chars = [];
            const charMap = [];
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null
            );

            const appendSpace = () => {
                if (chars.length > 0 && chars[chars.length - 1] !== " ") {
                    chars.push(" ");
                    charMap.push(null);
                }
            };

            let node;
            while ((node = walker.nextNode())) {
                const parent = node.parentElement;
                if (!parent) continue;
                if (["SCRIPT", "STYLE", "NOSCRIPT"].includes(parent.tagName)) {
                    continue;
                }
                if (!node.nodeValue) continue;

                for (let offset = 0; offset < node.nodeValue.length; offset += 1) {
                    const character = node.nodeValue[offset];
                    if (/\\s/.test(character)) {
                        appendSpace();
                    } else {
                        chars.push(character);
                        charMap.push({ node, offset });
                    }
                }
                appendSpace();
            }

            const haystack = chars.join("");
            const needle = text.replace(/\\s+/g, " ").trim();
            const start = haystack
                .toLocaleLowerCase()
                .indexOf(needle.toLocaleLowerCase(), state.index);
            if (start < 0 || start + needle.length > charMap.length) {
                window.__webToolsFindState = state;
                return false;
            }

            let startMap = null;
            let endMap = null;
            for (let index = start; index < start + needle.length; index += 1) {
                if (charMap[index]) {
                    startMap = charMap[index];
                    break;
                }
            }
            for (let index = start + needle.length - 1; index >= start; index -= 1) {
                if (charMap[index]) {
                    endMap = charMap[index];
                    break;
                }
            }
            if (!startMap || !endMap) {
                window.__webToolsFindState = state;
                return false;
            }

            const range = document.createRange();
            range.setStart(startMap.node, startMap.offset);
            range.setEnd(endMap.node, endMap.offset + 1);

            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);

            state.index = start + 1;
            window.__webToolsFindState = state;
            return true;
        }
        """,
        text,
    )


async def extract_match_boxes(page: Page, js_script: str) -> dict | None:
    """Evaluate the JS helper to extract word-level boxes for the selection."""
    return await page.evaluate(js_script)


async def capture_viewport_screenshot(page: Page) -> bytes:
    """Capture a screenshot of the current viewport."""
    return await page.screenshot(full_page=False)


def annotate_screenshot_with_boxes(
    screenshot_bytes: bytes,
    boxes: list[dict],
) -> Image.Image:
    """Overlay bounding boxes on a screenshot and return the annotated image."""
    image = Image.open(io.BytesIO(screenshot_bytes))
    elements = convert_js_boxes_to_page_elements(boxes, image.width, image.height)
    response = annotate(image, elements)
    return response.response_data


async def scroll_element_into_view(page: Page, selector: str, index: int) -> bool:
    """Scroll the nth visible element matching selector into view."""
    js_code = """
    ([selector, targetIndex]) => {
        const elements = document.querySelectorAll(selector);
        let visibleIndex = 0;
        for (const el of elements) {
            const rect = el.getBoundingClientRect();
            // Skip tiny images (icons, trackers)
            if (selector === 'img' && (rect.width < 10 || rect.height < 10)) continue;
            if (rect.width === 0 || rect.height === 0) continue;
            if (visibleIndex === targetIndex) {
                el.scrollIntoView({ block: 'center', behavior: 'instant' });
                return true;
            }
            visibleIndex++;
        }
        return false;
    }
    """
    return await page.evaluate(js_code, [selector, index])


async def get_element_bbox(page: Page, selector: str, index: int) -> dict | None:
    """Return bbox info for nth visible element."""
    js_code = """
    ([selector, targetIndex]) => {
        const elements = document.querySelectorAll(selector);
        let visibleIndex = 0;
        for (const el of elements) {
            const rect = el.getBoundingClientRect();
            // Skip tiny images (icons, trackers)
            if (selector === 'img' && (rect.width < 10 || rect.height < 10)) continue;
            if (rect.width === 0 || rect.height === 0) continue;
            if (visibleIndex === targetIndex) {
                const scrollX = window.scrollX || window.pageXOffset;
                const scrollY = window.scrollY || window.pageYOffset;
                return {
                    bbox: {
                        x: rect.left + scrollX,
                        y: rect.top + scrollY,
                        width: rect.width,
                        height: rect.height
                    },
                    viewport_bbox: {
                        x: rect.left,
                        y: rect.top,
                        width: rect.width,
                        height: rect.height
                    },
                    viewport_size: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    }
                };
            }
            visibleIndex++;
        }
        return null;
    }
    """
    return await page.evaluate(js_code, [selector, index])


def clamp_bbox_to_viewport(viewport_bbox: dict, viewport_size: dict) -> dict:
    """Clamp a viewport-relative bbox to the viewport bounds."""
    return {
        "x": max(0, viewport_bbox["x"]),
        "y": max(0, viewport_bbox["y"]),
        "width": min(
            viewport_bbox["width"], viewport_size["width"] - max(0, viewport_bbox["x"])
        ),
        "height": min(
            viewport_bbox["height"],
            viewport_size["height"] - max(0, viewport_bbox["y"]),
        ),
    }


def annotate_screenshot_with_bbox(
    screenshot_bytes: bytes,
    clamped_bbox: dict,
    *,
    label: str,
) -> Image.Image:
    """Overlay a single bbox on a screenshot and return the annotated image."""
    image = Image.open(io.BytesIO(screenshot_bytes))
    if clamped_bbox["width"] <= 0 or clamped_bbox["height"] <= 0:
        return image

    elements = convert_js_boxes_to_page_elements(
        [clamped_bbox],
        image.width,
        image.height,
    )
    elements[0] = PageElement(content=label, coord=elements[0].coord)
    response = annotate(image, elements)
    return response.response_data


async def find_visual_element_on_page(
    page: Page,
    *,
    element_id: str,
    element_type: VisualElementType,
    selector: str,
    index: int,
) -> VisualElementMatch | None:
    """Find a visual element on the page and return bbox + annotated image."""
    if not await scroll_element_into_view(page, selector, index):
        return None

    await page.wait_for_timeout(150)
    result = await get_element_bbox(page, selector, index)
    if not result:
        return None

    screenshot_bytes = await page.screenshot(full_page=False)
    clamped_bbox = clamp_bbox_to_viewport(
        result["viewport_bbox"],
        result["viewport_size"],
    )
    annotated_image = annotate_screenshot_with_bbox(
        screenshot_bytes,
        clamped_bbox,
        label=element_id,
    )

    return VisualElementMatch(
        id=element_id,
        element_type=element_type,
        bbox=result["bbox"],
        image=annotated_image,
    )
