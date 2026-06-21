"""Shared setup for runnable web tools e2e modules.

Why:
    Centralizes manual e2e execution setup at the e2e package level.

When to use:
    Imported automatically when running e2e scenarios in module mode, for
    example:
        uv run python -m \
            tests.web_tools.e2e.fetch_cache_and_page_artifacts.test_cache_behavior
"""

from __future__ import annotations

import sys
from pathlib import Path

from py_lib_tooling import configure_direct_module_process, get_project_tooling_config

_PROJECT_CONFIG = get_project_tooling_config()

configure_direct_module_process(
    main_file=getattr(sys.modules.get("__main__"), "__file__", None),
    package_root=Path(__file__).resolve().parent,
    configure_logging_from_env=_PROJECT_CONFIG.env_var("LOG_LEVEL"),
)
