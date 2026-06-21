"""Root pytest configuration for reusable test infrastructure.

Why:
    Keeps repository-wide pytest setup independent from the product package so
    this file can remain a portable backbone for future libraries.

When to use:
    Put only generic pytest hooks and fixtures here. Package-specific fixtures
    belong under the package test tree, for example `tests/<package>/`.
"""

from __future__ import annotations

from typing import Any

import pytest
from py_lib_tooling import configure_pytest_process
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension

configure_pytest_process()


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    """Configure VCR for HTTP recording."""
    return {
        "filter_headers": [
            "authorization",
            "x-api-key",
            "api-key",
        ],
        "match_on": ["method", "scheme", "host", "port", "path", "body"],
    }


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Use JSON format for readable snapshots."""
    return snapshot.use_extension(JSONSnapshotExtension)
