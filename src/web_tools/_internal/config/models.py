"""Runtime configuration models.

Why:
    Defines immutable config snapshots consumed by the private runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from py_lib_runtime import (
    validate_non_negative_int,
    validate_positive_float,
    validate_positive_int,
)

from web_tools._api import defaults as api_defaults
from web_tools._internal.config.validation import (
    coerce_allowed_media_types,
    coerce_media_config,
    validate_boolean_option,
    validate_user_agent,
)


@dataclass(frozen=True, slots=True)
class MediaConfig:
    """Configuration for media downloading."""

    enabled: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_ENABLED
    allowed_types: tuple[str, ...] = api_defaults.DEFAULT_MEDIA_DOWNLOAD_ALLOWED_TYPES
    max_file_size_mb: float = api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_FILE_SIZE_MB
    max_downloads_per_post: int = (
        api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_DOWNLOADS_PER_POST
    )
    max_total_downloads: int = api_defaults.DEFAULT_MEDIA_DOWNLOAD_MAX_TOTAL_DOWNLOADS
    cache_media: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_CACHE_MEDIA
    download_thumbnails: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_DOWNLOAD_THUMBNAILS
    skip_head: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_SKIP_HEAD
    use_proxy_for_small: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_SMALL
    use_proxy_for_large: bool = api_defaults.DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_LARGE
    proxy_size_threshold_mb: float = (
        api_defaults.DEFAULT_MEDIA_DOWNLOAD_PROXY_SIZE_THRESHOLD_MB
    )

    def __post_init__(self) -> None:
        """Validate and freeze media download config values."""
        object.__setattr__(
            self,
            "allowed_types",
            coerce_allowed_media_types(self.allowed_types),
        )

        for field_name in (
            "enabled",
            "cache_media",
            "download_thumbnails",
            "skip_head",
            "use_proxy_for_small",
            "use_proxy_for_large",
        ):
            object.__setattr__(
                self,
                field_name,
                validate_boolean_option(
                    field_name=f"MediaConfig.{field_name}",
                    value=getattr(self, field_name),
                ),
            )

        for field_name in ("max_file_size_mb", "proxy_size_threshold_mb"):
            object.__setattr__(
                self,
                field_name,
                validate_positive_float(
                    field_name=f"MediaConfig.{field_name}",
                    value=getattr(self, field_name),
                ),
            )

        for field_name in ("max_downloads_per_post", "max_total_downloads"):
            object.__setattr__(
                self,
                field_name,
                validate_non_negative_int(
                    field_name=f"MediaConfig.{field_name}",
                    value=getattr(self, field_name),
                ),
            )


@dataclass(frozen=True, slots=True)
class WebToolsConfig:
    """Validated runtime configuration for `web_tools`."""

    timeout_seconds: float = api_defaults.DEFAULT_TIMEOUT_SECONDS
    viewport_width: int = api_defaults.DEFAULT_VIEWPORT_WIDTH
    viewport_height: int = api_defaults.DEFAULT_VIEWPORT_HEIGHT
    cache_max_size_bytes: int = api_defaults.DEFAULT_CACHE_MAX_SIZE_BYTES
    user_agent: str | None = api_defaults.DEFAULT_USER_AGENT
    media_cache_max_size_bytes: int = api_defaults.DEFAULT_MEDIA_CACHE_MAX_SIZE_BYTES
    media_proxy_timeout_seconds: float = (
        api_defaults.DEFAULT_MEDIA_PROXY_TIMEOUT_SECONDS
    )
    media_direct_timeout_seconds: float = (
        api_defaults.DEFAULT_MEDIA_DIRECT_TIMEOUT_SECONDS
    )
    media_download: MediaConfig = field(default_factory=MediaConfig)

    def __post_init__(self) -> None:
        """Validate and freeze runtime config values."""
        for field_name in (
            "timeout_seconds",
            "media_proxy_timeout_seconds",
            "media_direct_timeout_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                validate_positive_float(
                    field_name=f"WebToolsConfig.{field_name}",
                    value=getattr(self, field_name),
                ),
            )

        for field_name in (
            "viewport_width",
            "viewport_height",
            "cache_max_size_bytes",
            "media_cache_max_size_bytes",
        ):
            object.__setattr__(
                self,
                field_name,
                validate_positive_int(
                    field_name=f"WebToolsConfig.{field_name}",
                    value=getattr(self, field_name),
                ),
            )

        object.__setattr__(self, "user_agent", validate_user_agent(self.user_agent))
        object.__setattr__(
            self,
            "media_download",
            coerce_media_config(self.media_download),
        )


@dataclass(frozen=True, slots=True)
class ResolvedWebToolsDefaults:
    """Resolved defaults derived from public configuration declarations."""

    timeout_seconds: float
    viewport_width: int
    viewport_height: int
    user_agent: str | None
    cache_max_size_bytes: int
    media_cache_max_size_bytes: int
    media_proxy_timeout_seconds: float
    media_direct_timeout_seconds: float
    media_download: MediaConfig
