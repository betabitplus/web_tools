"""Runtime configuration package.

Why:
    Owns validated immutable configuration snapshots for private runtime
    instances.

What belongs here:
    Config dataclasses, default assembly, validation, and process-wide snapshot
    state.

What does not belong here:
    Public facade helpers, browser/cache internals, or media download runtime.
"""

from web_tools._internal.config.assembly import (
    build_default_config as build_default_config,
)
from web_tools._internal.config.models import (
    MediaConfig as MediaConfig,
    ResolvedWebToolsDefaults as ResolvedWebToolsDefaults,
    WebToolsConfig as WebToolsConfig,
)
from web_tools._internal.config.state import (
    WebToolsResolver as WebToolsResolver,
    get_default_web_tools_resolver as get_default_web_tools_resolver,
    get_web_tools_config as get_web_tools_config,
    install_web_tools_config as install_web_tools_config,
)
from web_tools._internal.config.validation import validate_config as validate_config
