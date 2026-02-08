"""
Tests for get_climate_status Tool
==================================

This test suite validates the get_climate_status() consolidated adapter method and MCP tool registration.

What is tested:
- Electric vehicle climate status (active heating scenario)
- Combustion vehicle climate status (off scenario)
- Climatization states (off, heating, cooling, ventilation)
- Target temperature validation and realistic ranges
- Window heating status (front and rear)
- is_active consistency with climatization state
- Estimated time remaining for active climatization
- Data completeness validation
- Invalid vehicle handling
- MCP server tool registration (get_climatization_state, get_window_heating_state)

Key features:
- Consolidated method replaces multiple old methods (get_climatization_state, get_window_heating_state)
- Unified climate model with climatization and window heating
- State consistency validation (off state = not active)
- Realistic temperature ranges (15-30°C)

Test data:
- Electric vehicle: Active heating at 22°C, rear window heating on
- Combustion vehicle: Climatization off, all heating off
"""
import pytest
from test_data import (
    VIN_ELECTRIC,
    VIN_COMBUSTION,
    VIN_INVALID,
    EXPECTED_CLIMATE_ELECTRIC,
    EXPECTED_CLIMATE_COMBUSTION,
)


# ==================== TESTS - ELECTRIC VEHICLE (ACTIVE HEATING) ====================

def test_get_climate_status_electric_vehicle(adapter):
    """Test getting climate status for electric vehicle with active heating"""
    climate = adapter.get_climate_status(VIN_ELECTRIC)
    
    assert climate is not None
    assert climate.climatization is not None
    assert climate.window_heating is not None


def test_climate_status_electric_active_heating(adapter):
    """Test that electric vehicle has active heating"""
    climate = adapter.get_climate_status(VIN_ELECTRIC)
    
    assert climate.climatization.state == EXPECTED_CLIMATE_ELECTRIC["climatization_state"]
    assert climate.climatization.is_active == EXPECTED_CLIMATE_ELECTRIC["is_active"]
    assert climate.climatization.target_temperature_celsius == EXPECTED_CLIMATE_ELECTRIC["target_temperature_celsius"]


def test_climate_status_electric_window_heating(adapter):
    """Test electric vehicle window heating status"""
    climate = adapter.get_climate_status(VIN_ELECTRIC)
    
    assert climate.window_heating is not None
    assert climate.window_heating.rear.state == EXPECTED_CLIMATE_ELECTRIC["window_heating_rear"]


def test_climate_status_electric_estimated_time(adapter):
    """Test that active heating has estimated time remaining"""
    climate = adapter.get_climate_status(VIN_ELECTRIC)
    
    if climate.climatization.is_active:
        # When active, should have estimated time
        assert climate.climatization.estimated_time_remaining_minutes is not None
        assert climate.climatization.estimated_time_remaining_minutes > 0


# ==================== TESTS - COMBUSTION VEHICLE (OFF) ====================

def test_get_climate_status_combustion_vehicle(adapter):
    """Test getting climate status for combustion vehicle (off)"""
    climate = adapter.get_climate_status(VIN_COMBUSTION)
    
    assert climate is not None
    assert climate.climatization is not None
    assert climate.window_heating is not None


def test_climate_status_combustion_off(adapter):
    """Test that combustion vehicle climatization is off"""
    climate = adapter.get_climate_status(VIN_COMBUSTION)
    
    assert climate.climatization.state == EXPECTED_CLIMATE_COMBUSTION["climatization_state"]
    assert climate.climatization.is_active == EXPECTED_CLIMATE_COMBUSTION["is_active"]
    assert climate.climatization.target_temperature_celsius == EXPECTED_CLIMATE_COMBUSTION["target_temperature_celsius"]


def test_climate_status_combustion_window_heating_off(adapter):
    """Test that combustion vehicle window heating is off"""
    climate = adapter.get_climate_status(VIN_COMBUSTION)
    
    assert climate.window_heating.rear.state == EXPECTED_CLIMATE_COMBUSTION["window_heating_rear"]


def test_climate_status_combustion_no_estimated_time_when_off(adapter):
    """Test that inactive climatization has no estimated time"""
    climate = adapter.get_climate_status(VIN_COMBUSTION)
    
    if not climate.climatization.is_active:
        # When inactive, estimated time should be None
        assert climate.climatization.estimated_time_remaining_minutes is None


# ==================== TESTS - CLIMATIZATION STATES ====================

def test_climate_status_state_is_valid(adapter):
    """Test that climatization state is one of valid values"""
    electric_climate = adapter.get_climate_status(VIN_ELECTRIC)
    combustion_climate = adapter.get_climate_status(VIN_COMBUSTION)
    
    valid_states = ["off", "heating", "cooling", "ventilation"]
    
    assert electric_climate.climatization.state in valid_states
    assert combustion_climate.climatization.state in valid_states


def test_climate_status_active_state_consistency(adapter):
    """Test that is_active matches state (off = not active)"""
    electric_climate = adapter.get_climate_status(VIN_ELECTRIC)
    combustion_climate = adapter.get_climate_status(VIN_COMBUSTION)
    
    # If state is "off", is_active should be False
    if electric_climate.climatization.state == "off":
        assert electric_climate.climatization.is_active is False
    
    if combustion_climate.climatization.state == "off":
        assert combustion_climate.climatization.is_active is False


# ==================== TESTS - TEMPERATURE ====================

def test_climate_status_temperature_in_realistic_range(adapter):
    """Test that target temperature is in realistic range"""
    electric_climate = adapter.get_climate_status(VIN_ELECTRIC)
    combustion_climate = adapter.get_climate_status(VIN_COMBUSTION)
    
    # Realistic cabin temperature: 15-30°C
    assert 15 <= electric_climate.climatization.target_temperature_celsius <= 30
    assert 15 <= combustion_climate.climatization.target_temperature_celsius <= 30


# ==================== TESTS - WINDOW HEATING ====================

def test_climate_status_window_heating_has_front_and_rear(adapter):
    """Test that window heating has both front and rear"""
    climate = adapter.get_climate_status(VIN_ELECTRIC)
    
    assert climate.window_heating.front is not None
    assert climate.window_heating.rear is not None


def test_climate_status_window_heating_state_is_valid(adapter):
    """Test that window heating state is valid"""
    climate = adapter.get_climate_status(VIN_ELECTRIC)
    
    valid_states = ["on", "off"]
    
    assert climate.window_heating.front.state in valid_states
    assert climate.window_heating.rear.state in valid_states


# ==================== TESTS - INVALID VEHICLE ====================

def test_get_climate_status_invalid_vehicle(adapter):
    """Test that invalid vehicle returns None"""
    climate = adapter.get_climate_status(VIN_INVALID)
    
    assert climate is None


# ==================== TESTS - DATA COMPLETENESS ====================

def test_climate_status_has_all_climatization_fields(adapter):
    """Test that climatization has all expected fields"""
    climate = adapter.get_climate_status(VIN_ELECTRIC)
    
    assert climate.climatization.state is not None
    assert climate.climatization.is_active is not None
    assert climate.climatization.target_temperature_celsius is not None


def test_climate_status_has_all_window_heating_fields(adapter):
    """Test that window heating has all expected fields"""
    climate = adapter.get_climate_status(VIN_ELECTRIC)
    
    assert climate.window_heating.front is not None
    assert climate.window_heating.rear is not None
    assert climate.window_heating.front.state is not None
    assert climate.window_heating.rear.state is not None


# ==================== TESTS - COMPARE VEHICLES ====================

def test_climate_status_different_between_vehicles(adapter):
    """Test that climate status differs between electric and combustion"""
    electric_climate = adapter.get_climate_status(VIN_ELECTRIC)
    combustion_climate = adapter.get_climate_status(VIN_COMBUSTION)
    
    # Electric has heating active, combustion is off
    assert electric_climate.climatization.is_active != combustion_climate.climatization.is_active


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_get_climate_status_tools_are_registered(mcp_server):
    """Test that climate status tools are registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    
    # Check that the climate-related tools are registered
    # (these are the current MCP tools that provide climate status)
    assert "get_climatization_state" in tool_names, "get_climatization_state tool should be registered"
    assert "get_window_heating_state" in tool_names, "get_window_heating_state tool should be registered"
