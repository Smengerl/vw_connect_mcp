"""
Tests for the AdapterUnavailableError translation chain
==========================================================

Covers the two small decorators added for ARCHITECTURE.md §2.4's
"server_unavailable" handling:

- tibber_adapter._translate_auth_errors: any TibberAuthError ->
  AdapterUnavailableError (backend-agnostic port exception), carrying the
  same error_type code through.
- read_tools._handle_unavailable: AdapterUnavailableError -> a JSON
  {"error": "server_unavailable", "error_type": ..., ...} tool response
  instead of a raw framework-level error.

Tested as plain decorators against dummy functions -- no real adapter or
MCP server needed, matching this suite's fast/offline unit-test style.
"""
import json

import pytest

from weconnect_mcp.adapter.abstract_adapter import AdapterUnavailableError
from weconnect_mcp.adapter.tibber_adapter import _translate_auth_errors
from weconnect_mcp.adapter.tibber_client import TibberAuthError
from weconnect_mcp.server.mixins.read_tools import _handle_unavailable


# ==================== tibber_adapter._translate_auth_errors ====================

def test_translate_auth_errors_converts_reauth_required():
    @_translate_auth_errors
    def boom():
        raise TibberAuthError("reauth needed", error_type="reauth_required")

    with pytest.raises(AdapterUnavailableError, match="reauth needed") as exc_info:
        boom()
    assert exc_info.value.error_type == "reauth_required"


@pytest.mark.parametrize(
    "error_type",
    ["not_configured", "invalid_client", "reauth_required", "network_error", "unavailable"],
)
def test_translate_auth_errors_converts_every_error_type(error_type):
    """Every TibberAuthError error_type must reach the MCP client as a
    clean server_unavailable response carrying that same code, instead of
    escaping as a raw exception that crashes the tool call (the bug this
    decorator used to have when it only caught a single reauth-required
    subclass, back when each error_type had its own exception class)."""
    @_translate_auth_errors
    def boom():
        raise TibberAuthError("something went wrong", error_type=error_type)

    with pytest.raises(AdapterUnavailableError) as exc_info:
        boom()
    assert exc_info.value.error_type == error_type


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
        raise AdapterUnavailableError(
            "Tibber authorization has expired and needs manual re-authorization",
            error_type="reauth_required",
        )

    result = json.loads(flaky())
    assert result["error"] == "server_unavailable"
    assert result["error_type"] == "reauth_required"
    assert "expired" in result["message"]


def test_handle_unavailable_defaults_error_type_to_unavailable():
    @_handle_unavailable
    def flaky():
        raise AdapterUnavailableError("something broke")

    result = json.loads(flaky())
    assert result["error_type"] == "unavailable"


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
