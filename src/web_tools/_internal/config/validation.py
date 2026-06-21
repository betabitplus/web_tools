"""Runtime config validation helpers.

Why:
    Centralizes config normalization and invariant checks before snapshots are
    constructed or installed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from py_lib_runtime import (
    validate_non_negative_int,
    validate_positive_float,
    validate_positive_int,
)

from web_tools._api.defaults import SUPPORTED_MEDIA_DOWNLOAD_TYPES
from web_tools._api.errors import InvalidConfigValueError
from web_tools._api.types import MediaType

if TYPE_CHECKING:
    from web_tools._internal.config.models import MediaConfig, WebToolsConfig


def validate_boolean_option(*, field_name: str, value: object) -> bool:
    """Reject non-boolean config values at the construction boundary."""
    if isinstance(value, bool):
        return value
    raise InvalidConfigValueError(
        field=field_name,
        value=value,
        reason="must be a boolean",
    )


def _coerce_allowed_media_type_name(value: object) -> str:
    """Return one public media type name from caller-provided config input."""
    if isinstance(value, MediaType):
        return value.value
    if isinstance(value, str):
        return value
    raise InvalidConfigValueError(
        field="allowed_types",
        value=value,
        reason="must contain only media type strings",
    )


def coerce_allowed_media_types(value: object) -> tuple[str, ...]:
    """Return a tuple snapshot of caller-provided media type names."""
    if isinstance(value, set):
        allowed_types = tuple(
            _coerce_allowed_media_type_name(item) for item in sorted(value, key=str)
        )
    elif isinstance(value, list | tuple):
        allowed_types = tuple(_coerce_allowed_media_type_name(item) for item in value)
    else:
        raise InvalidConfigValueError(
            field="allowed_types",
            value=value,
            reason="must be a list, set, or tuple of media type strings",
        )

    invalid_types = tuple(
        media_type
        for media_type in allowed_types
        if media_type not in SUPPORTED_MEDIA_DOWNLOAD_TYPES
    )
    if invalid_types:
        raise InvalidConfigValueError(
            field="allowed_types",
            value=invalid_types,
            reason=f"must be one of {list(SUPPORTED_MEDIA_DOWNLOAD_TYPES)}",
        )
    return allowed_types


def validate_user_agent(value: object) -> str | None:
    """Validate user-agent config when provided."""
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise InvalidConfigValueError(
            field="user_agent",
            value=value,
            reason="must be a non-empty string when provided",
        )
    return value


def coerce_media_config(value: object) -> MediaConfig:
    """Return a media config snapshot from caller-provided input."""
    from web_tools._internal.config.models import MediaConfig

    if isinstance(value, MediaConfig):
        return value
    if isinstance(value, Mapping):
        return MediaConfig(**dict(value))
    raise InvalidConfigValueError(
        field="media_download",
        value=value,
        reason="must be a MediaConfig or mapping",
    )


def validate_media_config(config: MediaConfig) -> None:
    """Validate one media download config snapshot."""
    coerce_allowed_media_types(config.allowed_types)
    for field_name in (
        "enabled",
        "cache_media",
        "download_thumbnails",
        "skip_head",
        "use_proxy_for_small",
        "use_proxy_for_large",
    ):
        validate_boolean_option(
            field_name=f"MediaConfig.{field_name}",
            value=getattr(config, field_name),
        )
    for field_name in ("max_file_size_mb", "proxy_size_threshold_mb"):
        validate_positive_float(
            field_name=f"MediaConfig.{field_name}",
            value=getattr(config, field_name),
        )
    for field_name in ("max_downloads_per_post", "max_total_downloads"):
        validate_non_negative_int(
            field_name=f"MediaConfig.{field_name}",
            value=getattr(config, field_name),
        )


def validate_config(config: WebToolsConfig) -> None:
    """Validate one runtime config snapshot."""
    for field_name in (
        "timeout_seconds",
        "media_proxy_timeout_seconds",
        "media_direct_timeout_seconds",
    ):
        validate_positive_float(
            field_name=f"WebToolsConfig.{field_name}",
            value=getattr(config, field_name),
        )
    for field_name in (
        "viewport_width",
        "viewport_height",
        "cache_max_size_bytes",
        "media_cache_max_size_bytes",
    ):
        validate_positive_int(
            field_name=f"WebToolsConfig.{field_name}",
            value=getattr(config, field_name),
        )
    validate_user_agent(config.user_agent)
    validate_media_config(coerce_media_config(config.media_download))
