"""Offline public-contract checks for configuration objects."""

from __future__ import annotations

import pytest

from web_tools import (
    MediaConfig,
    MediaDownloader,
    MediaType,
    WebToolsConfig,
    WebToolsError,
    get_web_tools_config,
    install_web_tools_config,
)

# =============================================================================
# Tests
# =============================================================================


def test_media_config_normalizes_allowed_types_sequence() -> None:
    """Media download types are normalized to an immutable tuple."""
    config = MediaConfig(allowed_types=["image", "video"])

    assert config.allowed_types == ("image", "video")


def test_media_config_accepts_public_media_type_vocabulary() -> None:
    """Public media type vocabulary can be used in config input."""
    config = MediaConfig(allowed_types=[MediaType.IMAGE, MediaType.VIDEO])

    assert config.allowed_types == ("image", "video")


def test_media_config_rejects_unknown_allowed_type() -> None:
    """Unknown media download types fail at config construction."""
    with pytest.raises(WebToolsError, match="allowed_types"):
        MediaConfig(allowed_types=["audio"])


def test_media_config_rejects_non_string_allowed_type() -> None:
    """Allowed media types must remain public string vocabulary values."""
    with pytest.raises(WebToolsError, match="media type strings"):
        MediaConfig(allowed_types=[object()])


def test_web_tools_config_is_top_level_public_config() -> None:
    """Runtime config declarations are available from the public entrypoint."""
    config = WebToolsConfig()

    assert config.timeout_seconds > 0
    assert isinstance(config.media_download, MediaConfig)


def test_install_web_tools_config_replaces_public_snapshot() -> None:
    """Installed config snapshots are returned by the public config reader."""
    config = WebToolsConfig(timeout_seconds=12.5, viewport_width=1440)

    installed = install_web_tools_config(config)

    assert installed is config
    assert get_web_tools_config() is config


def test_install_web_tools_config_rejects_unknown_snapshot_type() -> None:
    """Only validated web_tools config snapshots can be installed."""
    with pytest.raises(TypeError, match="WebToolsConfig"):
        install_web_tools_config(object())


def test_installed_web_tools_config_updates_default_media_runtime() -> None:
    """Installing config invalidates default runtime objects built before it."""
    old_downloader = MediaDownloader(cache_dir=None)
    old_downloader.close()
    config = WebToolsConfig(
        media_download=MediaConfig(enabled=False, allowed_types=["gif"]),
    )

    install_web_tools_config(config)
    downloader = MediaDownloader(cache_dir=None)

    try:
        assert downloader.config.allowed_types == ("gif",)
    finally:
        downloader.close()
