"""
Tests for the AdapterUnavailableError translation chain
==========================================================

Covers the two small decorators added for ARCHITECTURE.md §2.4's
"server_unavailable" handling:

- tibber_adapter._translate_auth_errors: TibberReauthRequiredError (Tibber-
  specific) -> AdapterUnavailableError (backend-agnostic port exception).
- read_tools._handle_unavailable: AdapterUnavailableError -> a JSON
  {"error": "server_unavailable", ...} tool response instead of a raw
  framework-level error.

Tested as plain decorators against dummy functions -- no real adapter or
MCP server needed, matching this suite's fast/offline unit-test style.
"""
import json

import pytest

from weconnect_mcp.adapter.abstract_adapter import AdapterUnavailableError
from weconnect_mcp.adapter.tibber_adapter import _translate_auth_errors
from weconnect_mcp.adapter.tibber_client import TibberReauthRequiredError
from weconnect_mcp.server.mixins.read_tools import _handle_unavailable


# ==================== tibber_adapter._translate_auth_errors ====================

def test_translate_auth_errors_converts_reauth_required():
    @_translate_auth_errors
    def boom():
        raise TibberReauthRequiredError("reauth needed")

    with pytest.raises(AdapterUnavailableError, match="reauth needed"):
        boom()


def test_translate_auth_errors_passes_through_success():
    @_translate_auth_errors
    def ok():
        return 42

    assert ok() == 42


def test_translate_auth_errors_leaves_other_exceptions_alone():
    @_translate_auth_errors
    def broken():
        raise ValueError("unrelated")

    with pytest.raises(ValueError):
        broken()


# ==================== read_tools._handle_unavailable ====================

def test_handle_unavailable_wraps_error_as_json():
    @_handle_unavailable
    def flaky():
        raise AdapterUnavailableError("Tibber authorization has expired and needs manual re-authorization")

    result = json.loads(flaky())
    assert result["error"] == "server_unavailable"
    assert "expired" in result["message"]


def test_handle_unavailable_passes_through_success():
    @_handle_unavailable
    def ok():
        return "hello"

    assert ok() == "hello"


def test_handle_unavailable_leaves_other_exceptions_alone():
    @_handle_unavailable
    def broken():
        raise ValueError("unrelated")

    with pytest.raises(ValueError):
        broken()
