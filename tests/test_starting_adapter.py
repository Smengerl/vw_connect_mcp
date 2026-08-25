"""
Tests for UnavailableAdapter (starting_adapter.py)
=====================================================

Covers the stub used when the real Tibber adapter couldn't be built at
all -- no cached tokens, invalid client credentials, or a refresh that was
genuinely rejected (see ARCHITECTURE.md §2.4). Every method must raise
AdapterUnavailableError with the given message/error_type, so the MCP
server can still start and register its tools instead of the process
crashing before any client connects.

ReconnectingAdapter (which wraps this) has its own dedicated test file,
test_reconnecting_adapter.py.
"""
import pytest

from weconnect_mcp.adapter.abstract_adapter import AdapterUnavailableError
from weconnect_mcp.adapter.starting_adapter import UnavailableAdapter

MESSAGE = "Tibber authorization has expired, run tibber_login_cli"


def test_list_vehicles_raises_with_message():
    with pytest.raises(AdapterUnavailableError, match=MESSAGE):
        UnavailableAdapter(MESSAGE).list_vehicles()


def test_get_vehicle_raises_with_message():
    with pytest.raises(AdapterUnavailableError, match=MESSAGE):
        UnavailableAdapter(MESSAGE).get_vehicle("some-vin")


def test_get_energy_status_raises_with_message():
    with pytest.raises(AdapterUnavailableError, match=MESSAGE):
        UnavailableAdapter(MESSAGE).get_energy_status("some-vin")


def test_shutdown_and_context_manager_are_no_ops():
    with UnavailableAdapter(MESSAGE) as adapter:
        adapter.shutdown()  # must not raise


def test_error_type_defaults_to_unavailable():
    assert UnavailableAdapter(MESSAGE).error_type == "unavailable"


def test_error_type_is_propagated_into_adapter_unavailable_error():
    adapter = UnavailableAdapter(MESSAGE, error_type="not_configured")
    assert adapter.error_type == "not_configured"
    with pytest.raises(AdapterUnavailableError) as exc_info:
        adapter.list_vehicles()
    assert exc_info.value.error_type == "not_configured"
