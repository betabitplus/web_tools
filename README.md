# web-tools

Standalone Python library for web content fetching, HTML-to-Markdown conversion,
visual element manifests, text quoting, element quoting, and media download
helpers.

## Public API

- `html2html(...)` cleans raw HTML into readable HTML.
- `html2md(...)` converts HTML into Markdown plus a visual element manifest.
- `fetch_html(...)` fetches page HTML with optional page-artifact caching.
- `quote_text(...)` finds text on a page and returns annotated screenshots.
- `quote_element(...)` finds visual elements such as `P_0`, `T_1`, or `M_0`.
- `MediaDownloader` downloads media URLs from post-like payloads.
- `MediaConfig` and `WebToolsConfig` describe caller-facing configuration.
- `MediaType` and `VisualElementType` provide stable public vocabulary.

## Quickstart

```bash
uv sync --group dev
uv run py-lib-smoke-public-api
uv run pytest tests/web_tools -m "not slow" -q
```

```python
from web_tools import html2md

response = html2md("<article><h1>Hello</h1><p>World</p></article>")
print(response.markdown)
print(response.manifest.counts)
```

## Repository Shape

- `src/web_tools/` contains the shipped package.
- `src/web_tools/_api/` contains public declarations and thin facades.
- `src/web_tools/_internal/` contains private implementation.
- `tests/web_tools/` contains package-specific verification.
- `workbench/web_tools/` contains manual probes that do not import the shipped package.
- `docs/web_tools/` contains package architecture, usage, and verification notes.
- Shared test and repo tooling comes from `py-lib-tooling`.
- Shared runtime support comes from `py-lib-runtime`.

## Documentation

- [Setup](SETUP.md)
- [Contributing](CONTRIBUTING.md)
- [Web tools docs](docs/web_tools/README.md)
