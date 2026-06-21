# %%
"""Shared e2e replay fixtures for `web_tools` tests."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from py_lib_tooling import (
    require_vcr_cassette_or_record_mode,
)


def _is_loopback_address(address: object) -> bool:
    """Return true when a socket target is local-only."""
    if not isinstance(address, tuple) or not address:
        return True

    host = address[0]
    if not isinstance(host, str):
        return False
    if host == "localhost":
        return True

    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def deny_external_python_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail pytest-side e2e network calls unless they target loopback."""
    original_connect = socket.socket.connect

    def guarded_connect(self: socket.socket, address: object) -> object:
        """Reject non-loopback socket connections during hermetic pytest runs."""
        if not _is_loopback_address(address):
            pytest.fail(
                reason=f"External network call blocked during e2e pytest: {address}",
                pytrace=False,
            )
        return original_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)


@pytest.fixture(autouse=True)
def require_vcr_replay_or_record_mode(request: pytest.FixtureRequest) -> None:
    """Fail VCR tests unless replay data exists or recording is explicit."""
    if request.node.get_closest_marker("vcr") is None:
        return

    node_path = getattr(request.node, "path", None)
    if node_path is None:
        return

    original_name = getattr(request.node, "originalname", None)
    test_name = original_name if isinstance(original_name, str) else request.node.name
    test_name = test_name.split("[", maxsplit=1)[0]
    require_vcr_cassette_or_record_mode(
        test_file=str(node_path),
        test_name=test_name,
    )


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves replay fixtures without noisy request logs."""

    def log_message(self, format_string: str, *args: object) -> None:
        """Suppress per-request access logs during e2e tests."""
        _ = format_string, args


@pytest.fixture(scope="session")
def e2e_site_url() -> Iterator[str]:
    """Serve committed replay fixtures from a loopback-only HTTP server."""
    fixture_root = Path(__file__).resolve().parent / "fixtures" / "site"
    handler = partial(_QuietStaticHandler, directory=str(fixture_root))

    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/index.html"
        finally:
            server.shutdown()
            thread.join(timeout=5)
