"""
Tests for get_energy_status Tool
=================================

This test suite validates the get_energy_status() consolidated adapter method and MCP tool registration.

What is tested:
- Electric vehicle energy status (battery level, charging state, electric range)
- Combustion vehicle energy status (tank level, fuel type, combustion range)
- Range information and consistency
- Charging state details (is_charging, is_plugged_in, charging_power_kw)
- Vehicle type awareness (electric vs combustion data separation)
- Data completeness validation
- Invalid vehicle handling
- MCP server tool registration (get_charging_state, get_range_info, get_battery_status)

Key features:
- Consolidated method replaces multiple old methods (get_charging_state, get_range_info, get_battery_status)
- Vehicle type-specific data (electric.battery_level vs combustion.tank_level)
- Unified range model with electric_km and combustion_km fields
- Charging information only for electric/hybrid vehicles

Test data:
- Electric vehicle: ID.7 Tourer with 80% battery, 312km range
- Combustion vehicle: Transporter 7 with 68% tank, 650km range
"""
import pytest
from test_data import (
    VIN_ELECTRIC,
    VIN_COMBUSTION,
    VIN_INVALID,
    EXPECTED_ENERGY_ELECTRIC,
    EXPECTED_ENERGY_COMBUSTION,
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


# ==================== TESTS - COMBUSTION VEHICLE ====================

def test_get_energy_status_combustion_vehicle(adapter):
    """Test getting energy status for combustion vehicle"""
    energy = adapter.get_energy_status(VIN_COMBUSTION)
    
    assert energy is not None
    assert energy.vehicle_type == "combustion"
    assert energy.electric is None
    assert energy.combustion is not None


def test_energy_status_combustion_tank_level(adapter):
    """Test combustion vehicle fuel tank level"""
    energy = adapter.get_energy_status(VIN_COMBUSTION)
    
    assert energy.combustion is not None
    assert energy.combustion.tank_level_percent == EXPECTED_ENERGY_COMBUSTION["tank_level_percent"]
    assert 0 <= energy.combustion.tank_level_percent <= 100


def test_energy_status_combustion_range(adapter):
    """Test combustion vehicle range information"""
    energy = adapter.get_energy_status(VIN_COMBUSTION)
    
    assert energy.range is not None
    assert energy.range.total_km == EXPECTED_ENERGY_COMBUSTION["total_range_km"]
    assert energy.range.combustion_km == EXPECTED_ENERGY_COMBUSTION["combustion_range_km"]
    assert energy.range.electric_km is None or energy.range.electric_km == 0


def test_energy_status_combustion_fuel_type(adapter):
    """Test combustion vehicle fuel type"""
    energy = adapter.get_energy_status(VIN_COMBUSTION)
    
    assert energy.combustion is not None
    # Fuel type should be set for combustion vehicles
    assert energy.combustion.fuel_type is not None
    assert energy.combustion.fuel_type in ["diesel", "petrol", "gasoline", "cng", "lpg"]


# ==================== TESTS - RANGE VALIDITY ====================

def test_energy_status_range_is_positive(adapter):
    """Test that range values are positive"""
    electric_energy = adapter.get_energy_status(VIN_ELECTRIC)
    combustion_energy = adapter.get_energy_status(VIN_COMBUSTION)
    
    assert electric_energy.range.total_km > 0
    assert electric_energy.range.electric_km > 0
    
    assert combustion_energy.range.total_km > 0
    assert combustion_energy.range.combustion_km > 0


def test_energy_status_range_consistency(adapter):
    """Test that electric range equals total range for BEV"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)
    
    # For pure electric vehicles, total range should equal electric range
    assert energy.range.total_km == energy.range.electric_km


# ==================== TESTS - CHARGING STATE ====================

def test_energy_status_charging_information(adapter):
    """Test charging state and power information"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)
    
    # Charging state should be boolean
    assert energy.electric.charging.is_charging in [True, False]
    assert energy.electric.charging.is_plugged_in in [True, False]
    
    # Power only relevant when charging
    if energy.electric.charging.is_charging:
        assert energy.electric.charging.charging_power_kw is not None
        assert energy.electric.charging.charging_power_kw > 0
    # If not charging, power can be None or 0


# ==================== TESTS - INVALID VEHICLE ====================

def test_get_energy_status_invalid_vehicle(adapter):
    """Test that invalid vehicle returns None"""
    energy = adapter.get_energy_status(VIN_INVALID)
    
    assert energy is None


# ==================== TESTS - VEHICLE TYPE AWARENESS ====================

def test_energy_status_vehicle_type_matches_data(adapter):
    """Test that vehicle_type field matches the actual data returned"""
    electric_energy = adapter.get_energy_status(VIN_ELECTRIC)
    combustion_energy = adapter.get_energy_status(VIN_COMBUSTION)
    
    # Electric should have electric data only
    assert electric_energy.vehicle_type == "electric"
    assert electric_energy.electric is not None
    assert electric_energy.combustion is None
    
    # Combustion should have combustion data only
    assert combustion_energy.vehicle_type == "combustion"
    assert combustion_energy.combustion is not None
    assert combustion_energy.electric is None


# ==================== TESTS - DATA COMPLETENESS ====================

def test_energy_status_has_complete_electric_data(adapter):
    """Test that electric vehicle has all expected fields"""
    energy = adapter.get_energy_status(VIN_ELECTRIC)
    
    assert energy.electric.battery_level_percent is not None
    assert energy.electric.charging is not None
    assert energy.range is not None
    assert energy.range.total_km is not None
    assert energy.range.electric_km is not None


def test_energy_status_has_complete_combustion_data(adapter):
    """Test that combustion vehicle has all expected fields"""
    energy = adapter.get_energy_status(VIN_COMBUSTION)
    
    assert energy.combustion.tank_level_percent is not None
    assert energy.combustion.fuel_type is not None
    assert energy.range is not None
    assert energy.range.total_km is not None
    assert energy.range.combustion_km is not None


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_get_energy_status_tools_are_registered(mcp_server):
    """Test that energy status resources are registered in the MCP server"""
    resource_templates = await mcp_server.get_resource_templates()
    
    assert resource_templates is not None, "Resource templates should not be None"
    template_uris = list(resource_templates.keys())
    
    # Check that the energy-related resources are registered
    # (these are the current MCP resources that provide energy status)
    assert "data://vehicle/{vehicle_id}/charging" in template_uris, "data://vehicle/{vehicle_id}/charging resource should be registered"
    assert "data://vehicle/{vehicle_id}/range" in template_uris, "data://vehicle/{vehicle_id}/range resource should be registered"
    assert "data://vehicle/{vehicle_id}/battery" in template_uris, "data://vehicle/{vehicle_id}/battery resource should be registered"
