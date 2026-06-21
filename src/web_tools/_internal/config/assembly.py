"""Built-in config assembly.

Why:
    Converts public default declarations into validated private config snapshots
    before runtime work begins.
"""

from __future__ import annotations

from py_lib_runtime import get_logger

from web_tools._api import defaults as api_defaults
from web_tools._internal.config.models import MediaConfig, WebToolsConfig
from web_tools._internal.config.validation import validate_config

logger = get_logger(__name__)


def build_default_config() -> WebToolsConfig:
    """Assemble and validate the built-in runtime config snapshot."""
    config = WebToolsConfig(
        timeout_seconds=api_defaults.DEFAULT_TIMEOUT_SECONDS,
        viewport_width=api_defaults.DEFAULT_VIEWPORT_WIDTH,
        viewport_height=api_defaults.DEFAULT_VIEWPORT_HEIGHT,
        cache_max_size_bytes=api_defaults.DEFAULT_CACHE_MAX_SIZE_BYTES,
        user_agent=api_defaults.DEFAULT_USER_AGENT,
        media_cache_max_size_bytes=api_defaults.DEFAULT_MEDIA_CACHE_MAX_SIZE_BYTES,
        media_proxy_timeout_seconds=api_defaults.DEFAULT_MEDIA_PROXY_TIMEOUT_SECONDS,
        media_direct_timeout_seconds=api_defaults.DEFAULT_MEDIA_DIRECT_TIMEOUT_SECONDS,
        media_download=MediaConfig(
            enabled=api_defaults.DEFAULT_MEDIA_DOWNLOAD_ENABLED,
            allowed_types=api_defaults.DEFAULT_MEDIA_DOWNLOAD_ALLOWED_TYPES,
            max_file_size_mb=api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_FILE_SIZE_MB,
            max_downloads_per_post=(
                api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_DOWNLOADS_PER_POST
            ),
            max_total_downloads=api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_TOTAL_DOWNLOADS,
            cache_media=api_defaults.DEFAULT_MEDIA_DOWNLOAD_CACHE_MEDIA,
            download_thumbnails=(
                api_defaults.DEFAULT_MEDIA_DOWNLOAD_DOWNLOAD_THUMBNAILS
            ),
            skip_head=api_defaults.DEFAULT_MEDIA_DOWNLOAD_SKIP_HEAD,
            use_proxy_for_small=api_defaults.DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_SMALL,
            use_proxy_for_large=api_defaults.DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_LARGE,
            proxy_size_threshold_mb=(
                api_defaults.DEFAULT_MEDIA_DOWNLOAD_PROXY_SIZE_THRESHOLD_MB
            ),
        ),
    )
    validate_config(config)
    logger.info(
        "Runtime config resolved",
        event_type="web_tools.config.runtime.resolved",
        timeout_seconds=config.timeout_seconds,
        cache_max_size_bytes=config.cache_max_size_bytes,
        media_enabled=config.media_download.enabled,
    )
    return config
