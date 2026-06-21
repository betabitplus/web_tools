---
name: architecture-concepts
doc_type: index
description: Index of the architecture concept slices for web_tools. Use when you need one focused runtime slice at a time.
---

# Concepts

## Overview

These docs describe the primary vertical slices of the `web_tools` runtime
model. Each file owns one stable product slice rather than one mechanism-only
topic.

## Files

- [html-conversion-and-visual-manifest.md](html-conversion-and-visual-manifest.md)
  Explains readable HTML, Markdown conversion, and visual element IDs.
  Use it to understand why converted output can become page evidence.
- [fetch-cache-and-page-artifacts.md](fetch-cache-and-page-artifacts.md)
  Explains URL fetching, cache evidence, and page artifact ownership.
  Use it to understand why page retrieval stays explicit and replayable.
- [quote-text-and-elements.md](quote-text-and-elements.md)
  Explains text and visual-element quoting as public screenshot evidence.
  Use it to understand why evidence workflows stay tied to public inputs.
- [media-extraction-and-download-policy.md](media-extraction-and-download-policy.md)
  Explains post-like media extraction and download policy.
  Use it to understand why media work stays policy-driven.
- [public-boundary-and-errors.md](public-boundary-and-errors.md)
  Explains the normalized output boundary and public error surface.
  Use it to understand why callers see stable DTOs and exceptions.
