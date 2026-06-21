"""Private implementation root for `web_tools`.

Why:
    Re-exports private runtime entrypoints so `_api` facades import through one
    private root instead of deep implementation modules.
"""

from __future__ import annotations

from web_tools._internal.config import (
    MediaConfig as MediaConfig,
    WebToolsConfig as WebToolsConfig,
    get_web_tools_config as get_web_tools_config,
    install_web_tools_config as install_web_tools_config,
)
from web_tools._internal.media_downloader.service import (
    MediaDownloader as _MediaDownloaderRuntime,
)
from web_tools._internal.runtime.facade import (
    build_fetch_response as build_fetch_response,
    build_markdown_response as build_markdown_response,
    build_quote_element_match as build_quote_element_match,
    build_quote_text_matches as build_quote_text_matches,
    build_readable_html as build_readable_html,
    configure_page_cache_from_user_path as configure_page_cache_from_user_path,
)

MediaDownloaderRuntime = _MediaDownloaderRuntime
