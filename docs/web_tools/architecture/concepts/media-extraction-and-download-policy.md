---
name: media-extraction-and-download-policy
doc_type: architecture
description: High-level media extraction and download policy model for web_tools. Use when you need to understand how post-like payloads become config-gated media results.
---

# Media Extraction And Download Policy

## Overview

This document describes how `web_tools` extracts media candidates from
post-like payloads and downloads only the items allowed by public policy.

Question this diagram answers: How does post-like media input become
policy-gated public media output?

```mermaid
flowchart LR
    Post["Post-Like Payload"] --> Extract["Extract Candidate URLs"]
    Extract --> Classify["Classify Media Type"]
    Classify --> Policy["Apply MediaConfig"]
    Policy --> Download["Download Or Skip"]
    Download --> Items["MediaItem Results"]
```

## Main Model

### Public Downloader Boundary

- `MediaDownloader` is the public media facade and owns a validated
  `MediaConfig` snapshot.
- Callers may use it as a context manager to make resource cleanup explicit.
- The public methods expose URL extraction, single URL download,
  post-payload download, stats, and close behavior.

### Media Policy Boundary

- `MediaConfig` controls whether downloading is enabled, which media types are
  allowed, file-size limits, per-post limits, total limits, cache behavior, and
  proxy preferences.
- Public `MediaType` names define caller vocabulary; private runtime code may
  map those names to extensions, content types, or host rules.
- Disabled or limit-blocked downloads should produce predictable empty results
  or skipped items rather than surprising network behavior.

### Media Result Boundary

- `MediaItem` carries URL, bytes, content type, extension, size, cache evidence,
  and optional timestamp.
- Media cache entries and downloader stats are observability details over the
  public workflow, not a replacement for returned media items.
- Transport errors are translated into public media errors before crossing the
  package boundary.

## Rules

- Media extraction and download policy must be visible through public config,
  not hidden global switches.
- Downloaded media must cross the public boundary as `MediaItem` values.
- Private host, extension, proxy, HTTP, and cache mechanics must not become
  caller requirements.
