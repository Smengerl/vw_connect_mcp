"""
Tests for get_energy_status Tool
=================================

This test suite validates the get_energy_status() consolidated adapter method and MCP tool registration.

What is tested:
- Electric vehicle energy status (battery level, charging state, electric range)
- Hybrid vehicle energy status (battery + tank level, electric + combustion range)
- Range information and consistency
- Charging state details (is_charging, is_plugged_in)
- Vehicle type awareness (electric vs hybrid data shape)
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
- Vehicle type-specific data (electric.battery_level vs combustion.tank_level)
- Unified range model with electric_km and combustion_km fields
- Charging information only for electric/hybrid vehicles

Test data:
- Electric vehicle: ID.7 Tourer with 80% battery, 312km range
- Hybrid vehicle: T7 Multivan eHybrid with 64% battery + 72% tank, 630km
  combined range -- both electric and combustion data present at once,
  since a real PHEV has both (unlike a pure BEV or a pure ICE vehicle,
  which Tibber never reports at all -- see ARCHITECTURE.md)
"""
from test_data import (
    VIN_ELECTRIC,
    VIN_HYBRID,
    VIN_INVALID,
    EXPECTED_ENERGY_ELECTRIC,
    EXPECTED_ENERGY_HYBRID,
)


# ==================== TESTS - ELECTRIC VEHICLE ====================

def test_get_energy_status_electric_vehicle(adapter):
    """Test getting energy status for electric vehicle"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)
    
    assert energy is not None
    assert energy.vehicle_type == "electric"
    assert energy.electric is not None
    assert energy.combustion is None


def test_energy_status_electric_battery_level(adapter):
    """Test electric vehicle battery level"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)
    
    assert energy.electric is not None
    assert energy.electric.battery_level_percent == EXPECTED_ENERGY_ELECTRIC["battery_level_percent"]
    assert 0 <= energy.electric.battery_level_percent <= 100


def test_energy_status_electric_range(adapter):
    """Test electric vehicle range information"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)
    
    assert energy.range is not None
    assert energy.range.total_km == EXPECTED_ENERGY_ELECTRIC["total_range_km"]
    assert energy.range.electric_km == EXPECTED_ENERGY_ELECTRIC["electric_range_km"]
    assert energy.range.combustion_km is None or energy.range.combustion_km == 0


def test_energy_status_electric_charging(adapter):
    """Test electric vehicle charging information"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    assert energy.electric is not None
    assert energy.electric.charging is not None
    assert hasattr(energy.electric.charging, 'is_charging')
    assert hasattr(energy.electric.charging, 'is_plugged_in')


def test_energy_status_electric_last_seen(adapter):
    """Test electric vehicle last-seen timestamp (Tibber's status.lastSeen)"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)

    assert energy.last_seen == EXPECTED_ENERGY_ELECTRIC["last_seen"]


# ==================== TESTS - HYBRID VEHICLE ====================

def test_get_energy_status_hybrid_vehicle(adapter):
    """Test getting energy status for a plug-in hybrid vehicle"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy is not None
    assert energy.vehicle_type == "hybrid"
    # Unlike a pure BEV or pure ICE, a PHEV has both populated at once.
    assert energy.electric is not None
    assert energy.combustion is not None


def test_energy_status_hybrid_battery_level(adapter):
    """Test hybrid vehicle battery level"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.electric is not None
    assert energy.electric.battery_level_percent == EXPECTED_ENERGY_HYBRID["battery_level_percent"]
    assert 0 <= energy.electric.battery_level_percent <= 100


def test_energy_status_hybrid_tank_level(adapter):
    """Test hybrid vehicle fuel tank level"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.combustion is not None
    assert energy.combustion.tank_level_percent == EXPECTED_ENERGY_HYBRID["tank_level_percent"]
    assert 0 <= energy.combustion.tank_level_percent <= 100


def test_energy_status_hybrid_range(adapter):
    """Test hybrid vehicle range information (electric + combustion, both non-zero)"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.range is not None
    assert energy.range.total_km == EXPECTED_ENERGY_HYBRID["total_range_km"]
    assert energy.range.electric_km == EXPECTED_ENERGY_HYBRID["electric_range_km"]
    assert energy.range.combustion_km == EXPECTED_ENERGY_HYBRID["combustion_range_km"]


def test_energy_status_hybrid_last_seen(adapter):
    """Test hybrid vehicle last-seen timestamp (Tibber's status.lastSeen)"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.last_seen == EXPECTED_ENERGY_HYBRID["last_seen"]


def test_energy_status_hybrid_fuel_type(adapter):
    """Test hybrid vehicle fuel type"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.combustion is not None
    # Fuel type should be set whenever combustion data is present
    assert energy.combustion.fuel_type is not None
    assert energy.combustion.fuel_type in ["diesel", "petrol", "gasoline", "cng", "lpg"]


def test_energy_status_hybrid_charging(adapter):
    """Test hybrid vehicle charging information (plugged in, not currently charging)"""
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
    assert electric_energy.range.electric_km > 0

    assert hybrid_energy.range.total_km > 0
    assert hybrid_energy.range.electric_km > 0
    assert hybrid_energy.range.combustion_km > 0


def test_energy_status_range_consistency(adapter):
    """Test that electric range equals total range for BEV"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)
    
    # For pure electric vehicles, total range should equal electric range
    assert energy.range.total_km == energy.range.electric_km


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


# ==================== TESTS - VEHICLE TYPE AWARENESS ====================

def test_energy_status_vehicle_type_matches_data(adapter):
    """Test that vehicle_type field matches the actual data returned"""
    electric_energy = adapter.get_energy_status(VIN_ELECTRIC)
    hybrid_energy = adapter.get_energy_status(VIN_HYBRID)

    # Electric should have electric data only
    assert electric_energy.vehicle_type == "electric"
    assert electric_energy.electric is not None
    assert electric_energy.combustion is None

    # Hybrid should have both electric and combustion data
    assert hybrid_energy.vehicle_type == "hybrid"
    assert hybrid_energy.electric is not None
    assert hybrid_energy.combustion is not None


# ==================== TESTS - DATA COMPLETENESS ====================

def test_energy_status_has_complete_electric_data(adapter):
    """Test that electric vehicle has all expected fields"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)
    
    assert energy.electric.battery_level_percent is not None
    assert energy.electric.charging is not None
    assert energy.range is not None
    assert energy.range.total_km is not None
    assert energy.range.electric_km is not None


def test_energy_status_has_complete_hybrid_data(adapter):
    """Test that hybrid vehicle has all expected fields, electric and combustion alike"""
    energy = adapter.get_energy_status(VIN_HYBRID)

    assert energy.electric.battery_level_percent is not None
    assert energy.combustion.tank_level_percent is not None
    assert energy.combustion.fuel_type is not None
    assert energy.range is not None
    assert energy.range.total_km is not None
    assert energy.range.electric_km is not None
    assert energy.range.combustion_km is not None


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
