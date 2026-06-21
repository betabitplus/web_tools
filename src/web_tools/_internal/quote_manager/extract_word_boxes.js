/**
 * Extracts word-level bounding boxes for the currently selected text range.
 * Returns viewport-relative coordinates.
 */
function extractWordBoundingBoxes() {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) return null;

    const fullRange = sel.getRangeAt(0);
    const textNodes = getTextNodesInRange(fullRange);
    const charMap = buildCharacterMap(textNodes, fullRange);
    const words = tokenizeText(fullRange.toString());
    const boxes = getWordBoundingBoxes(words, charMap);

    return {
        chunk_text: fullRange.toString(),
        boxes: boxes
    };
}

/**
 * Gets all text nodes contained within a Range.
 * Uses TreeWalker instead of NodeIterator to avoid callback invalidation issues.
 */
function getTextNodesInRange(range) {
    const container = range.commonAncestorContainer;

    if (container.nodeType === Node.TEXT_NODE) {
        return [container];
    }

    const nodes = [];
    const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null  // No filter callback - filter manually instead
    );

    let node;
    while ((node = walker.nextNode())) {
        // Manually check if node intersects the range
        if (range.intersectsNode(node)) {
            nodes.push(node);
        }
    }
    return nodes;
}

/**
 * Builds a character-to-node mapping for precise word range creation.
 */
function buildCharacterMap(textNodes, fullRange) {
    const charMap = [];

    for (const node of textNodes) {
        const nodeText = node.nodeValue;
        const startOffset = (node === fullRange.startContainer) ? fullRange.startOffset : 0;
        const endOffset = (node === fullRange.endContainer) ? fullRange.endOffset : nodeText.length;

        for (let i = startOffset; i < endOffset; i++) {
            charMap.push({ node, offset: i });
        }
    }

    return charMap;
}

/**
 * Splits text into words with their character indices.
 */
function tokenizeText(text) {
    const words = [];
    const wordRegex = /\S+/g;
    let match;

    while ((match = wordRegex.exec(text)) !== null) {
        words.push({
            word: match[0],
            startIndex: match.index,
            endIndex: match.index + match[0].length
        });
    }

    return words;
}

/**
 * Creates bounding boxes for each word using the character map.
 */
function getWordBoundingBoxes(words, charMap) {
    const boxes = [];

    for (const w of words) {
        if (w.startIndex >= charMap.length || w.endIndex > charMap.length) continue;

        try {
            const startMap = charMap[w.startIndex];
            const endMap = charMap[w.endIndex - 1];

            const wordRange = document.createRange();
            wordRange.setStart(startMap.node, startMap.offset);
            wordRange.setEnd(endMap.node, endMap.offset + 1);

            const rects = wordRange.getClientRects();
            for (const rect of rects) {
                boxes.push({
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    word: w.word
                });
            }
        } catch (e) {
            console.warn(`[find_text_coords] Failed to create range for word "${w.word}":`, e.message);
        }
    }

    return boxes;
}

// Entry point - called from Python
extractWordBoundingBoxes();
