"""Public config re-exports.

Why:
    Keeps config names behind the `_api` facade while `_internal` owns config
    models, validation, runtime default resolution, and snapshot state.
"""

from __future__ import annotations

# pyright: reportUnusedImport=false
from web_tools._internal import (  # noqa: F401
    MediaConfig,
    WebToolsConfig,
    get_web_tools_config,
    install_web_tools_config,
)
