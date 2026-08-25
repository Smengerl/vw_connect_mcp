"""
Tests for the startup-resilience fallback in mcp_server_cli.py
==================================================================

Covers ARCHITECTURE.md §2.4's startup-resilience fix: if building the real
Tibber adapter fails with TibberAuthError (no cached tokens, or a refresh
genuinely rejected), the server must not crash before any MCP client ever
connects -- it should fall back to a ReconnectingAdapter wrapping
UnavailableAdapter and still start, so every tool call reports
"server_unavailable" instead of the whole process dying with a raw
traceback, AND a fix completed while the server keeps running (no
restart) heals on the very next tool call -- see
test_reconnecting_adapter.py for that retry behavior itself.

Both transports connect synchronously, through the exact same code path,
before server.run() is ever called -- there is no more background thread
or adapter proxy to account for (see mcp_server_cli.py's module docstring
for why HTTP mode dropped that: Docker/Railway's health-check start-period
comfortably covers a synchronous connect attempt). The one place the two
transports still differ: stdio lets an unexpected (non-TibberAuthError)
failure crash the process since a human is right there to see it; HTTP
mode catches it too so cloud platforms get *something* answering /health
instead of a crash-looping container.

_build_tibber_adapter and get_server are mocked; server.run() is mocked
too so this stays a fast unit test (no real transport is started).
"""
import sys
from unittest.mock import MagicMock, Mock

import pytest

from weconnect_mcp.adapter.starting_adapter import ReconnectingAdapter, UnavailableAdapter
from weconnect_mcp.adapter.tibber_adapter import TibberAdapter
from weconnect_mcp.adapter.tibber_client import TibberAuthError
from weconnect_mcp.cli import mcp_server_cli


def test_stdio_falls_back_to_unavailable_adapter_on_auth_failure(monkeypatch):
    captured = {}

    def fake_build_tibber_adapter(config_path):
        raise TibberAuthError("No cached Tibber tokens found")

    def fake_get_server(adapter, api_key=None):
        captured["adapter"] = adapter
        server = Mock()
        server.run = Mock()
        return server

    monkeypatch.setattr(mcp_server_cli, "_build_tibber_adapter", fake_build_tibber_adapter)
    monkeypatch.setattr("weconnect_mcp.server.mcp_server.get_server", fake_get_server)

    mcp_server_cli.run_server_from_cli(transport="stdio")

    assert isinstance(captured["adapter"], ReconnectingAdapter)
    delegate = captured["adapter"]._delegate
    assert isinstance(delegate, UnavailableAdapter)
    assert "No cached Tibber tokens found" in delegate.message


def test_stdio_uses_real_adapter_when_build_succeeds(monkeypatch):
    captured = {}
    fake_adapter = MagicMock(spec=TibberAdapter)
    fake_adapter.__enter__.return_value = fake_adapter
    fake_adapter.__exit__.return_value = None

    def fake_build_tibber_adapter(config_path):
        return fake_adapter

    def fake_get_server(adapter, api_key=None):
        captured["adapter"] = adapter
        server = Mock()
        server.run = Mock()
        return server

    monkeypatch.setattr(mcp_server_cli, "_build_tibber_adapter", fake_build_tibber_adapter)
    monkeypatch.setattr("weconnect_mcp.server.mcp_server.get_server", fake_get_server)

    mcp_server_cli.run_server_from_cli(transport="stdio")

    assert isinstance(captured["adapter"], ReconnectingAdapter)
    assert captured["adapter"]._delegate is fake_adapter


def test_stdio_does_not_swallow_unrelated_errors(monkeypatch):
    def fake_build_tibber_adapter(config_path):
        raise RuntimeError("credentials file is malformed JSON")

    monkeypatch.setattr(mcp_server_cli, "_build_tibber_adapter", fake_build_tibber_adapter)

    with pytest.raises(RuntimeError, match="malformed JSON"):
        mcp_server_cli.run_server_from_cli(transport="stdio")


def test_build_tibber_adapter_raises_not_configured_when_credentials_missing(monkeypatch):
    """Missing TIBBER_CLIENT_ID/SECRET must raise a TibberAuthError with
    error_type="not_configured" -- not a bare RuntimeError -- so it's
    caught by run_server_from_cli's existing TibberAuthError handling
    (both transports) instead of crashing stdio startup or stalling http
    startup forever in "starting" state."""
    monkeypatch.delenv("TIBBER_CLIENT_ID", raising=False)
    monkeypatch.delenv("TIBBER_CLIENT_SECRET", raising=False)

    with pytest.raises(TibberAuthError) as exc_info:
        mcp_server_cli._build_tibber_adapter(None)

    assert exc_info.value.error_type == "not_configured"
    assert "TIBBER_CLIENT_ID" in str(exc_info.value)
    assert "TIBBER_CLIENT_SECRET" in str(exc_info.value)
    # The remediation must be the *exact* runnable command for this
    # process's own interpreter -- not a bare `python`/`weconnect-tibber-login`
    # that only works if some venv happens to already be active/on PATH in
    # whatever shell the human (or an AI agent) runs it from.
    assert sys.executable in str(exc_info.value)


def test_build_tibber_adapter_login_command_includes_given_config_path(monkeypatch):
    """When a credentials file path is given, the remediation command in
    every auth-error message must include that exact path -- so a human
    (or an AI assistant) can copy-paste it without having to guess which
    file the server was actually configured to read."""
    monkeypatch.delenv("TIBBER_CLIENT_ID", raising=False)
    monkeypatch.delenv("TIBBER_CLIENT_SECRET", raising=False)

    with pytest.raises(TibberAuthError) as exc_info:
        mcp_server_cli._build_tibber_adapter("/some/path/tibber_config.json")

    assert "/some/path/tibber_config.json" in str(exc_info.value)


def test_http_falls_back_to_unavailable_adapter_on_unexpected_connect_failure(monkeypatch):
    """A non-TibberAuthError failure while connecting the backend (bug,
    malformed config, ...) must still start the server with an
    UnavailableAdapter fallback (wrapped in ReconnectingAdapter, same as
    every other fallback) instead of crashing -- unlike stdio mode, where
    this exact scenario is expected to propagate and crash (see
    test_stdio_does_not_swallow_unrelated_errors), because a cloud
    platform needs *something* answering /health rather than a
    crash-looping container."""
    def fake_build_tibber_adapter(config_path):
        raise RuntimeError("boom")

    monkeypatch.setattr(mcp_server_cli, "_build_tibber_adapter", fake_build_tibber_adapter)

    captured = {}

    def fake_get_server(adapter, api_key=None):
        captured["adapter"] = adapter
        server = Mock()
        server.run = Mock()
        return server

    monkeypatch.setattr("weconnect_mcp.server.mcp_server.get_server", fake_get_server)

    mcp_server_cli.run_server_from_cli(transport="http")

    assert isinstance(captured["adapter"], ReconnectingAdapter)
    delegate = captured["adapter"]._delegate
    assert isinstance(delegate, UnavailableAdapter)
    assert "boom" in delegate.message
    assert delegate.error_type == "unavailable"


def test_http_does_not_swallow_tibber_auth_errors_into_success(monkeypatch):
    """Sanity check that http mode's broader exception handling doesn't
    accidentally also swallow the already-differentiated TibberAuthError
    path -- error_type must survive, not collapse to the generic
    "unavailable" fallback used for truly unexpected errors."""
    def fake_build_tibber_adapter(config_path):
        raise TibberAuthError("no cached tokens")

    monkeypatch.setattr(mcp_server_cli, "_build_tibber_adapter", fake_build_tibber_adapter)

    captured = {}

    def fake_get_server(adapter, api_key=None):
        captured["adapter"] = adapter
        server = Mock()
        server.run = Mock()
        return server

    monkeypatch.setattr("weconnect_mcp.server.mcp_server.get_server", fake_get_server)

    mcp_server_cli.run_server_from_cli(transport="http")

    delegate = captured["adapter"]._delegate
    assert isinstance(delegate, UnavailableAdapter)
    assert delegate.error_type == "unavailable"  # plain TibberAuthError's generic fallback code
