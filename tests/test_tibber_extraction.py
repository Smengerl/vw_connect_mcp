"""Tests for the Tibber-specific data extraction logic.

TibberStateExtractionMixin and vin_from_external_id() are the two pieces
of genuinely Tibber-specific production logic in this project -- unlike
TibberAdapter itself (exercised indirectly through the tools/ tests via
TestAdapter), neither had any direct test coverage before. Both are pure
functions/methods with no I/O, so they're testable with fixture data taken
directly from ARCHITECTURE.md §3.1 (the real, confirmed device-detail
response shape) -- no network, no auth, no mock adapter needed.
"""

from weconnect_mcp.adapter.mixins.tibber_state_extraction_mixin import (
    TibberStateExtractionMixin,
)
from weconnect_mcp.adapter.tibber_client import vin_from_external_id

# The confirmed-live device-detail response shape from ARCHITECTURE.md §3.1.
DEVICE_DETAIL = {
    "capabilities": [
        {"id": "storage.stateOfCharge", "value": 74, "unit": "%"},
        {"id": "storage.targetStateOfCharge", "value": 80, "unit": "%"},
        {"id": "range.remaining", "value": 356000, "unit": "m"},
        {"id": "connector.status", "value": "disconnected"},
        {"id": "charging.status", "value": "idle"},
    ]
}


# ==================== vin_from_external_id() ====================

def test_vin_from_external_id_bare_vin():
    """Our confirmed VW/Enode-backed vehicle reports a bare VIN, no prefix."""
    assert vin_from_external_id("WVWZZZED4SE003938") == "WVWZZZED4SE003938"


def test_vin_from_external_id_vendor_prefixed():
    """Other Tibber-supported brands may use a vendor:VIN format (per evcc)."""
    assert vin_from_external_id("tesla:5YJSA1E26MF1234567") == "5YJSA1E26MF1234567"


def test_vin_from_external_id_empty_string():
    """An empty externalId should not raise."""
    assert vin_from_external_id("") == ""


# ==================== TibberStateExtractionMixin ====================

def test_charging_state_full_response():
    mixin = TibberStateExtractionMixin()
    charging = mixin._get_tibber_charging_state(DEVICE_DETAIL)

    assert charging is not None
    assert charging.current_soc_percent == 74.0
    assert charging.target_soc_percent == 80
    assert charging.is_plugged_in is False
    assert charging.is_charging is False
    assert charging.charging_state == "idle"
    # Confirmed not exposed by the Tibber Data API at all.
    assert charging.charging_power_kw is None
    assert charging.remaining_time_minutes is None
    assert charging.charge_mode is None


def test_charging_state_connected_and_charging():
    detail = {
        "capabilities": [
            {"id": "storage.stateOfCharge", "value": 42, "unit": "%"},
            {"id": "connector.status", "value": "connected"},
            {"id": "charging.status", "value": "charging"},
        ]
    }
    charging = TibberStateExtractionMixin()._get_tibber_charging_state(detail)

    assert charging.is_plugged_in is True
    assert charging.is_charging is True
    assert charging.current_soc_percent == 42.0


def test_charging_state_no_capabilities_returns_none():
    charging = TibberStateExtractionMixin()._get_tibber_charging_state({"capabilities": []})
    assert charging is None


def test_range_km_converts_meters():
    """range.remaining is reported in meters; the mixin must convert to km."""
    range_km = TibberStateExtractionMixin()._get_tibber_range_km(DEVICE_DETAIL)
    assert range_km == 356.0


def test_range_km_missing_capability_returns_none():
    range_km = TibberStateExtractionMixin()._get_tibber_range_km({"capabilities": []})
    assert range_km is None


def test_range_km_non_meter_unit_passthrough():
    """If a capability ever reports a non-'m' unit, don't apply the /1000 conversion."""
    detail = {"capabilities": [{"id": "range.remaining", "value": 250, "unit": "km"}]}
    assert TibberStateExtractionMixin()._get_tibber_range_km(detail) == 250.0
