---
name: e2e-verification
doc_type: index
description: Index of the hermetic e2e verification docs for web_tools. Use when you need the proof story for one focused e2e guarantee or workflow area.
---

# E2E Verification

## Overview

These docs describe what the hermetic e2e suite proves at the public boundary.
Each file follows one architecture concept slice so the proof structure stays
aligned with `architecture/concepts/` and `tests/web_tools/e2e/`.

## Files

- [html-conversion-and-visual-manifest.md](html-conversion-and-visual-manifest.md)
  Explains readable HTML, Markdown output, and visual manifest evidence.
  Use it to understand which conversion guarantees are proved end to end.
- [fetch-cache-and-page-artifacts.md](fetch-cache-and-page-artifacts.md)
  Explains fetch cache behavior and committed page artifact replay.
  Use it to understand why default e2e runs do not silently depend on the
  internet.
- [quote-text-and-elements.md](quote-text-and-elements.md)
  Explains text and visual-element screenshot evidence.
  Use it to understand which quote workflows are proved at the public boundary.
- [media-extraction-and-download-policy.md](media-extraction-and-download-policy.md)
  Explains the current media proof surface.
  Use it to understand what is proved offline today and what still lacks a
  dedicated e2e slice.
- [public-output-and-errors.md](public-output-and-errors.md)
  Explains public DTO, config, vocabulary, and boundary-direction guarantees.
  Use it to understand which terminal output and boundary rules callers can
  rely on.
