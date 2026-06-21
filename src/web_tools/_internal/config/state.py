"""Runtime config snapshot state.

Why:
    Keeps process-wide config construction, install/read helpers, and cached
    default resolution inside the private config implementation.
"""

from __future__ import annotations

from functools import cache
from threading import RLock

from py_lib_runtime import get_logger

from web_tools._internal.config.assembly import build_default_config
from web_tools._internal.config.models import ResolvedWebToolsDefaults, WebToolsConfig
from web_tools._internal.config.validation import validate_config

_installed_config: WebToolsConfig = build_default_config()
_config_lock = RLock()
logger = get_logger(__name__)


def get_web_tools_config(config: WebToolsConfig | None = None) -> WebToolsConfig:
    """Return a validated runtime configuration snapshot."""
    if config is not None:
        return config
    with _config_lock:
        return _installed_config


class WebToolsResolver:
    """Resolve optional runtime inputs against a validated config snapshot."""

    def __init__(self, config: WebToolsConfig | None = None) -> None:
        """Initialize the resolver from the installed config snapshot."""
        self._config = get_web_tools_config(config)

    @property
    def defaults(self) -> ResolvedWebToolsDefaults:
        """Return fully resolved defaults derived from configuration."""
        config = self._config
        return ResolvedWebToolsDefaults(
            timeout_seconds=config.timeout_seconds,
            viewport_width=config.viewport_width,
            viewport_height=config.viewport_height,
            user_agent=config.user_agent,
            cache_max_size_bytes=config.cache_max_size_bytes,
            media_cache_max_size_bytes=config.media_cache_max_size_bytes,
            media_proxy_timeout_seconds=config.media_proxy_timeout_seconds,
            media_direct_timeout_seconds=config.media_direct_timeout_seconds,
            media_download=config.media_download,
        )

    def resolve_timeout(self, timeout_sec: float | None) -> float:
        """Resolve a timeout override in seconds."""
        return self._config.timeout_seconds if timeout_sec is None else timeout_sec

    def resolve_user_agent(self, user_agent: str | None) -> str | None:
        """Resolve an optional user-agent override."""
        if user_agent is not None:
            return user_agent
        return self._config.user_agent

    def resolve_viewport(
        self,
        *,
        width: int | None = None,
        height: int | None = None,
    ) -> tuple[int, int]:
        """Resolve viewport width and height overrides."""
        config = self._config
        return (
            config.viewport_width if width is None else width,
            config.viewport_height if height is None else height,
        )


@cache
def get_default_web_tools_resolver() -> WebToolsResolver:
    """Return a cached default resolver."""
    return WebToolsResolver()


def install_web_tools_config(config: object) -> WebToolsConfig:
    """Install a validated runtime configuration snapshot."""
    if not isinstance(config, WebToolsConfig):
        msg = "install_web_tools_config() expects a WebToolsConfig instance."
        raise TypeError(msg)

    validate_config(config)
    global _installed_config  # noqa: PLW0603
    with _config_lock:
        _installed_config = config

    _clear_runtime_config_caches()
    logger.info(
        "Configuration installed",
        event_type="web_tools.config.runtime.installed",
        timeout_seconds=config.timeout_seconds,
        viewport_width=config.viewport_width,
        viewport_height=config.viewport_height,
        cache_max_size_bytes=config.cache_max_size_bytes,
        media_enabled=config.media_download.enabled,
    )
    return config


def _clear_runtime_config_caches() -> None:
    """Clear runtime objects that captured the previous config snapshot."""
    from web_tools._internal.cache.manager import clear_cache_instance

    clear_cache_instance()
    get_default_web_tools_resolver.cache_clear()
