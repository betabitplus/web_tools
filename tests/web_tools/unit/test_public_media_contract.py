"""Offline public-contract checks for media downloading."""

from __future__ import annotations

from web_tools import MediaConfig, MediaDownloader

# =============================================================================
# Tests
# =============================================================================


def test_media_downloader_exposes_public_config_snapshot() -> None:
    """The public downloader owns a validated media config snapshot."""
    config = MediaConfig(enabled=False)

    with MediaDownloader(config=config, cache_dir=None) as downloader:
        assert downloader.config == config
        assert downloader.download("https://i.redd.it/example.jpg") is None


def test_media_downloader_extracts_post_media_urls_without_downloads() -> None:
    """URL extraction is visible without requiring live network work."""
    downloader = MediaDownloader(config=MediaConfig(enabled=False), cache_dir=None)

    try:
        urls = downloader.extract_media_urls(
            {"url": "https://i.redd.it/example.jpg"},
        )

        assert urls == ["https://i.redd.it/example.jpg"]
        assert downloader.download_from_post({"url": urls[0]}) == []
        assert downloader.stats()["enabled"] is False
    finally:
        downloader.close()
