---
name: architecture
doc_type: index
description: Index of the stable architecture docs for web_tools. Use when you need high-level logic, flow, and boundary docs.
---

# Architecture

## Overview

These docs describe the integrated system model behind `web_tools` and the
focused architecture slices that deepen it. They intentionally avoid current
file layout and browser, parser, cache, or transport implementation detail.

## Files

- [system.md](system.md)
  Explains the integrated architecture story for one page-artifact workflow.
  Use it to understand how the main runtime slices fit together end to end.
- [concepts/README.md](concepts/README.md)
  Indexes the primary vertical-slice concept docs.
  Use it to choose one focused runtime model slice at a time.
- [flows/README.md](flows/README.md)
  Indexes the end-to-end flow docs.
  Use it to follow the page-artifact lifecycle from source to public evidence.
- [flows/page-artifact-lifecycle.md](flows/page-artifact-lifecycle.md)
  Explains how source HTML or a URL becomes caller-visible artifacts.
  Use it to understand why fetching, conversion, manifests, and quoting stay
  coherent.
- [concepts/html-conversion-and-visual-manifest.md](concepts/html-conversion-and-visual-manifest.md)
  Explains readable HTML, Markdown conversion, and visual element IDs.
  Use it to understand why converted output can later support element quoting.
- [concepts/fetch-cache-and-page-artifacts.md](concepts/fetch-cache-and-page-artifacts.md)
  Explains URL fetching, cache evidence, and page artifact ownership.
  Use it to understand why network retrieval and replayable page content stay
  explicit.
- [concepts/quote-text-and-elements.md](concepts/quote-text-and-elements.md)
  Explains text and visual-element quoting as public screenshot evidence.
  Use it to understand why page evidence stays tied to caller-visible inputs.
- [concepts/media-extraction-and-download-policy.md](concepts/media-extraction-and-download-policy.md)
  Explains post-like media extraction and download policy.
  Use it to understand why media handling stays policy-driven at the public
  boundary.
- [concepts/public-boundary-and-errors.md](concepts/public-boundary-and-errors.md)
  Explains the normalized output boundary and public error surface.
  Use it to understand why callers see stable DTOs and exceptions.
