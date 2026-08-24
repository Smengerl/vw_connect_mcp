"""
Tests for the stdio startup fallback in mcp_server_cli.py
============================================================

Covers ARCHITECTURE.md §2.4's startup-resilience fix: if building the real
Tibber adapter fails with TibberAuthError (no cached tokens, or a refresh
genuinely rejected), stdio mode must not crash before an MCP client ever
connects -- it should fall back to UnavailableAdapter and still start the
server, so every tool call reports "server_unavailable" instead of the
whole process dying with a raw traceback.

_build_tibber_adapter and get_server are mocked; server.run() is mocked
too so this stays a fast unit test (no real stdio transport is started).
"""
from unittest.mock import MagicMock, Mock

import pytest

from weconnect_mcp.adapter.starting_adapter import UnavailableAdapter
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

    assert isinstance(captured["adapter"], UnavailableAdapter)
    assert "No cached Tibber tokens found" in captured["adapter"]._message


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

    assert captured["adapter"] is fake_adapter


def test_stdio_does_not_swallow_unrelated_errors(monkeypatch):
    def fake_build_tibber_adapter(config_path):
        raise RuntimeError("credentials file is malformed JSON")

    monkeypatch.setattr(mcp_server_cli, "_build_tibber_adapter", fake_build_tibber_adapter)

    with pytest.raises(RuntimeError, match="malformed JSON"):
        mcp_server_cli.run_server_from_cli(transport="stdio")
