"""Built-in default declarations for `web_tools`.

Why:
    Keeps shared configuration defaults and small runtime catalogs in one
    declaration layer instead of scattering literals across config and
    implementation modules.

How:
    Treat these values as source declarations, not mutable runtime state.
    Runtime code is responsible for deriving concrete behavior such as media
    extension allow-lists and cache setup.

Notes:
    These values are consumed by `_api/config.py` and private runtime code. Raw
    default constants are intentionally not re-exported from the top-level
    package.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from web_tools._api.types import MediaType

# ================================================================================
# Core Runtime Defaults
# ================================================================================

# Range: >0 seconds
DEFAULT_TIMEOUT_SECONDS: float = 30.0
DEFAULT_USER_AGENT: str | None = None
# Range: >0 pixels
DEFAULT_VIEWPORT_HEIGHT: int = 1024
# Range: >0 pixels
DEFAULT_VIEWPORT_WIDTH: int = 1280

# ================================================================================
# Cache Defaults
# ================================================================================

# Range: >0 bytes
DEFAULT_CACHE_MAX_SIZE_BYTES: int = 1_073_741_824
# Range: >0 bytes
DEFAULT_MEDIA_CACHE_MAX_SIZE_BYTES: int = 209_715_200

# ================================================================================
# Media Transport Defaults
# ================================================================================

# Range: >0 seconds
DEFAULT_MEDIA_DIRECT_TIMEOUT_SECONDS: float = 60.0
# Range: >0 seconds
DEFAULT_MEDIA_PROXY_TIMEOUT_SECONDS: float = 30.0

# ================================================================================
# Media Download Defaults
# ================================================================================

MEDIA_TYPE_IMAGE: str = MediaType.IMAGE.value
MEDIA_TYPE_GIF: str = MediaType.GIF.value
MEDIA_TYPE_VIDEO: str = MediaType.VIDEO.value
MEDIA_TYPE_ALL: str = MediaType.ALL.value

SUPPORTED_MEDIA_DOWNLOAD_TYPES: tuple[str, ...] = (
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_GIF,
    MEDIA_TYPE_VIDEO,
    MEDIA_TYPE_ALL,
)

# Allowed values: image | gif | video | all
DEFAULT_MEDIA_DOWNLOAD_ALLOWED_TYPES: tuple[str, ...] = (MEDIA_TYPE_IMAGE,)
DEFAULT_MEDIA_DOWNLOAD_CACHE_MEDIA: bool = True
DEFAULT_MEDIA_DOWNLOAD_DOWNLOAD_THUMBNAILS: bool = False
DEFAULT_MEDIA_DOWNLOAD_ENABLED: bool = False
# Range: >=0 count
DEFAULT_MEDIA_DOWNLOAD_MAX_DOWNLOADS_PER_POST: int = 1
# Range: >0 megabytes
DEFAULT_MEDIA_DOWNLOAD_MAX_FILE_SIZE_MB: float = 5.0
# Range: >=0 count
DEFAULT_MEDIA_DOWNLOAD_MAX_TOTAL_DOWNLOADS: int = 10
# Range: >0 megabytes
DEFAULT_MEDIA_DOWNLOAD_PROXY_SIZE_THRESHOLD_MB: float = 2.0
DEFAULT_MEDIA_DOWNLOAD_SKIP_HEAD: bool = False
DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_LARGE: bool = False
DEFAULT_MEDIA_DOWNLOAD_USE_PROXY_FOR_SMALL: bool = True

# ================================================================================
# Media Catalog Defaults
# ================================================================================

MEDIA_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".bmp", ".jpeg", ".jpg", ".png", ".tiff", ".webp"}
)
MEDIA_GIF_EXTENSIONS: frozenset[str] = frozenset({".gif", ".gifv"})
MEDIA_VIDEO_EXTENSIONS: frozenset[str] = frozenset({".mov", ".mp4", ".webm"})
MEDIA_ALL_EXTENSIONS: frozenset[str] = frozenset(
    MEDIA_IMAGE_EXTENSIONS | MEDIA_GIF_EXTENSIONS | MEDIA_VIDEO_EXTENSIONS
)

MEDIA_TYPE_EXTENSIONS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        MEDIA_TYPE_IMAGE: MEDIA_IMAGE_EXTENSIONS,
        MEDIA_TYPE_GIF: MEDIA_GIF_EXTENSIONS,
        MEDIA_TYPE_VIDEO: MEDIA_VIDEO_EXTENSIONS,
        MEDIA_TYPE_ALL: MEDIA_ALL_EXTENSIONS,
    }
)

MEDIA_CONTENT_TYPE_EXTENSIONS: Mapping[str, str] = MappingProxyType(
    {
        "image/gif": ".gif",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
    }
)

MEDIA_HOST_SUFFIXES: frozenset[str] = frozenset(
    {"i.imgur.com", "i.redd.it", "preview.redd.it", "v.redd.it"}
)
