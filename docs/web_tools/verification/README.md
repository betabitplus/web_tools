---
name: verification
doc_type: index
description: Index of the verification-oriented docs for web_tools. Use when you need to find replay-backed e2e proof docs or live workbench validation docs.
---

# Verification

## Overview

These docs describe the main verification layers around `web_tools`:
offline public-contract tests, hermetic e2e proof, and live workbench
validation.

## Files

- [e2e/README.md](e2e/README.md)
  Indexes the hermetic concept-aligned e2e proof docs.
  Use it to find proof-oriented scenarios for one public behavior slice at a
  time.
- [public-boundary-and-errors.md](public-boundary-and-errors.md)
  Explains the public output, error, import, and smoke checks.
  Use it to understand how boundary drift is caught before callers see it.
- [workbench.md](workbench.md)
  Explains the live exploratory probes used for executable validation.
  Use it to understand when to run real integrations to inspect behavior that
  hermetic tests cannot fully answer.
