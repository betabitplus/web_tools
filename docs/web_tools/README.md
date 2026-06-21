---
name: web-tools-docs
doc_type: index
description: Index of the web_tools package docs. Use when you need the right package document.
---

# web_tools Docs

## Overview

These docs describe how `web_tools` exposes web-content workflows through one
stable public package boundary. Architecture docs define the durable vertical
slices; verification docs mirror those slices so proof coverage stays aligned
with the product model.

## Files

- [architecture/README.md](architecture/README.md)
  Indexes the stable architecture docs.
  Use it to navigate the integrated system model, concept slices, and runtime
  flows.
- [architecture/system.md](architecture/system.md)
  Explains how the main product slices fit together.
  Use it to understand the whole package model before reading focused docs.
- [dependencies.md](dependencies.md)
  Explains the role of the main runtime dependencies declared by the package.
  Use it to understand why each dependency exists and which slice it supports.
- [usage.md](usage.md)
  Shows representative caller workflows.
  Use it to write application code against the top-level package.
- [verification/README.md](verification/README.md)
  Indexes the verification-oriented docs.
  Use it to choose the right proof layer for unit, e2e, or live validation.
