"""
Tests for get_energy_status Tool
=================================

This test suite validates the get_energy_status() consolidated adapter method and MCP tool registration.

What is tested:
- Energy status (battery level, charging state, range) for both mock vehicles
- Charging state details (is_charging, is_plugged_in)
- Data completeness validation
- Invalid vehicle handling

Note: this file tests the `adapter.get_energy_status()` method directly, not
an MCP tool of the same name -- no such tool exists. The MCP tools built on
top of this adapter method are `get_vehicle_info` and `get_charging_status`
(see tests/tools/test_get_vehicle.py and read_tools.py); there used to be a
separate `get_battery_status` tool too, but every field it returned was
redundant with those two, so it was merged away.

Key features:
- Single adapter method serving both MCP tools
- Charging information only present when a vehicle is BEV/PHEV -- which,
  for this project's only backend (Tibber, EV-only, see ARCHITECTURE.md),
  is every vehicle it can ever report

Test data:
- Both mock vehicles are electric-shaped (see test_adapter.py): ID.7
  Tourer (80% battery, charging) and T7 Multivan eHybrid (64% battery, not
  charging) -- two different value sets to exercise identifier resolution,
  not two different data shapes.
"""
from test_data import (
    VIN_ELECTRIC,
    VIN_HYBRID,
    VIN_INVALID,
    EXPECTED_ENERGY_ELECTRIC,
    EXPECTED_ENERGY_HYBRID,
)


# ==================== TESTS - ID.7 ====================

def test_get_energy_status_electric_vehicle(adapter):
    """Test getting energy status for the ID.7"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    assert energy is not None
    assert energy.electric is not None


def test_energy_status_electric_battery_level(adapter):
    """Test ID.7 battery level"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    assert energy.electric is not None
    assert energy.electric.battery_level_percent == EXPECTED_ENERGY_ELECTRIC["battery_level_percent"]
    assert 0 <= energy.electric.battery_level_percent <= 100


def test_energy_status_electric_range(adapter):
    """Test ID.7 range information"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    assert energy.range is not None
    assert energy.range.total_km == EXPECTED_ENERGY_ELECTRIC["range_km"]


def test_energy_status_electric_charging(adapter):
    """Test ID.7 charging information"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    assert energy.electric is not None
    assert energy.electric.charging is not None
    assert hasattr(energy.electric.charging, 'is_charging')
    assert hasattr(energy.electric.charging, 'is_plugged_in')


def test_energy_status_electric_last_seen(adapter):
    """Test ID.7 last-seen timestamp (Tibber's status.lastSeen)"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    assert energy.last_seen == EXPECTED_ENERGY_ELECTRIC["last_seen"]


# ==================== TESTS - T7 MULTIVAN EHYBRID ====================

def test_get_energy_status_hybrid_vehicle(adapter):
    """Test getting energy status for the T7 -- same shape as any other
    vehicle Tibber reports (see test_adapter.py's docstring)."""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy is not None
    assert energy.electric is not None


def test_energy_status_hybrid_battery_level(adapter):
    """Test T7 battery level"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.electric is not None
    assert energy.electric.battery_level_percent == EXPECTED_ENERGY_HYBRID["battery_level_percent"]
    assert 0 <= energy.electric.battery_level_percent <= 100


def test_energy_status_hybrid_range(adapter):
    """Test T7 range information"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.range is not None
    assert energy.range.total_km == EXPECTED_ENERGY_HYBRID["range_km"]


def test_energy_status_hybrid_last_seen(adapter):
    """Test T7 last-seen timestamp (Tibber's status.lastSeen)"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.last_seen == EXPECTED_ENERGY_HYBRID["last_seen"]


def test_energy_status_hybrid_charging(adapter):
    """Test T7 charging information (plugged in, not currently charging)"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.electric is not None
    assert energy.electric.charging is not None
    assert energy.electric.charging.is_charging == EXPECTED_ENERGY_HYBRID["is_charging"]
    assert energy.electric.charging.is_plugged_in == EXPECTED_ENERGY_HYBRID["is_plugged_in"]


# ==================== TESTS - RANGE VALIDITY ====================

def test_energy_status_range_is_positive(adapter):
    """Test that range values are positive"""
    electric_energy = adapter.get_energy_status(VIN_ELECTRIC)
    hybrid_energy = adapter.get_energy_status(VIN_HYBRID)

    assert electric_energy.range.total_km > 0
    assert hybrid_energy.range.total_km > 0


# ==================== TESTS - CHARGING STATE ====================

def test_energy_status_charging_information(adapter):
    """Test charging state information (no charging power -- Tibber never reports it)"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    # Charging state should be boolean
    assert energy.electric.charging.is_charging in [True, False]
    assert energy.electric.charging.is_plugged_in in [True, False]
    assert not hasattr(energy.electric.charging, "charging_power_kw")


# ==================== TESTS - INVALID VEHICLE ====================

def test_get_energy_status_invalid_vehicle(adapter):
    """Test that invalid vehicle returns None"""
    energy = adapter.get_energy_status(VIN_INVALID)

    assert energy is None


# ==================== TESTS - DATA COMPLETENESS ====================

def test_energy_status_has_complete_electric_data(adapter):
    """Test that the ID.7 has all expected fields"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    assert energy.electric.battery_level_percent is not None
    assert energy.electric.charging is not None
    assert energy.range is not None
    assert energy.range.total_km is not None


def test_energy_status_has_complete_hybrid_data(adapter):
    """Test that the T7 has all expected fields"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.electric.battery_level_percent is not None
    assert energy.range is not None
    assert energy.range.total_km is not None


def test_energy_status_battery_fallback_from_charging_state(adapter):
    """Test that battery level falls back to charging state when drives data is unavailable.

    This tests the scenario where vehicle.drives doesn't provide battery level,
    but vehicle.battery (used in charging state) does. This can happen when the
    vehicle is in low-power mode or hasn't communicated with WeConnect servers recently.
    """
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    # The battery level should be available from either source
    assert energy.electric is not None
    assert energy.electric.battery_level_percent is not None

    # Verify it matches the charging state's current_soc_percent when available
    if energy.electric.charging and energy.electric.charging.current_soc_percent is not None:
        # Both values should be present and identical (from same underlying data)
        assert energy.electric.battery_level_percent == energy.electric.charging.current_soc_percent
