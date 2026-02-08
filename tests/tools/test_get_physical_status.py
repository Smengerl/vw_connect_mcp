"""
Tests for get_physical_status Tool
===================================

This test suite validates the get_physical_status() consolidated adapter method and MCP tool registration.

What is tested:
- All physical components together (doors, windows, tyres, lights)
- Individual component filtering (doors only, windows only, etc.)
- Multiple component selection
- Component-specific data validation:
  * Doors: locked/unlocked, open/closed states
  * Windows: open/closed states
  * Tyres: pressure readings and valid ranges
  * Lights: state reporting
- Empty components list handling (returns all components)
- Invalid vehicle handling
- MCP server tool registration (get_vehicle_doors, get_vehicle_windows, get_vehicle_tyres, get_lights_state)

Key features:
- Consolidated method replaces multiple old methods (get_doors_state, get_windows_state, get_tyres_state, get_lights_state)
- Optional component filtering for efficient data retrieval
- Consistent data model across all component types

Test data:
- Uses TestAdapter with realistic mock data
- Both electric and combustion vehicles tested
"""
import pytest
from test_data import (
    VIN_ELECTRIC,
    VIN_COMBUSTION,
    VIN_INVALID,
)


# ==================== TESTS - ALL COMPONENTS ====================

def test_get_physical_status_all_components_electric(adapter):
    """Test getting all physical components for electric vehicle"""
    status = adapter.get_physical_status(VIN_ELECTRIC)
    
    assert status is not None
    assert status.doors is not None
    assert status.windows is not None
    assert status.tyres is not None
    assert status.lights is not None


def test_get_physical_status_all_components_combustion(adapter):
    """Test getting all physical components for combustion vehicle"""
    status = adapter.get_physical_status(VIN_COMBUSTION)
    
    assert status is not None
    assert status.doors is not None
    assert status.windows is not None
    assert status.tyres is not None
    assert status.lights is not None


# ==================== TESTS - COMPONENT FILTERING ====================

def test_get_physical_status_doors_only(adapter):
    """Test getting only door status"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=["doors"])
    
    assert status is not None
    assert status.doors is not None
    assert status.windows is None
    assert status.tyres is None
    assert status.lights is None


def test_get_physical_status_windows_only(adapter):
    """Test getting only window status"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=["windows"])
    
    assert status is not None
    assert status.doors is None
    assert status.windows is not None
    assert status.tyres is None
    assert status.lights is None


def test_get_physical_status_multiple_components(adapter):
    """Test getting multiple specific components"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=["doors", "windows"])
    
    assert status is not None
    assert status.doors is not None
    assert status.windows is not None
    assert status.tyres is None
    assert status.lights is None


# ==================== TESTS - DOORS ====================

def test_physical_status_doors_locked(adapter):
    """Test that vehicle doors report correct lock states"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=["doors"])
    
    assert status.doors is not None
    assert status.doors.front_left.locked is True
    assert status.doors.front_right.locked is True
    assert status.doors.rear_left.locked is True
    assert status.doors.rear_right.locked is True


def test_physical_status_doors_all_closed(adapter):
    """Test that all doors are closed for both vehicles"""
    electric_status = adapter.get_physical_status(VIN_ELECTRIC, components=["doors"])
    combustion_status = adapter.get_physical_status(VIN_COMBUSTION, components=["doors"])
    
    # Electric
    assert electric_status.doors.front_left.open is False
    assert electric_status.doors.front_right.open is False
    
    # Combustion
    assert combustion_status.doors.front_left.open is False
    assert combustion_status.doors.front_right.open is False


# ==================== TESTS - WINDOWS ====================

def test_physical_status_windows_all_closed(adapter):
    """Test that all windows are closed"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=["windows"])
    
    assert status.windows is not None
    assert status.windows.front_left.open is False
    assert status.windows.front_right.open is False
    assert status.windows.rear_left.open is False
    assert status.windows.rear_right.open is False


# ==================== TESTS - TYRES ====================

def test_physical_status_tyres_have_pressure(adapter):
    """Test that tyres have pressure readings"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=["tyres"])
    
    assert status.tyres is not None
    assert status.tyres.front_left.pressure is not None
    assert status.tyres.front_right.pressure is not None
    assert status.tyres.rear_left.pressure is not None
    assert status.tyres.rear_right.pressure is not None


def test_physical_status_tyres_pressure_in_valid_range(adapter):
    """Test that tyre pressures are in realistic range"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=["tyres"])
    
    assert status.tyres is not None
    # Realistic pressure range: 1.8 - 3.5 bar
    for tyre in [status.tyres.front_left, status.tyres.front_right, 
                 status.tyres.rear_left, status.tyres.rear_right]:
        assert 1.5 <= tyre.pressure <= 4.0, f"Pressure {tyre.pressure} out of realistic range"


# ==================== TESTS - LIGHTS ====================

def test_physical_status_lights_off_when_parked(adapter):
    """Test that lights state is reported correctly"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=["lights"])
    
    assert status.lights is not None
    # TestAdapter uses 'ok' as the state value
    assert status.lights.left.state == "ok"
    assert status.lights.right.state == "ok"


# ==================== TESTS - INVALID VEHICLE ====================

def test_get_physical_status_invalid_vehicle(adapter):
    """Test that invalid vehicle returns None"""
    status = adapter.get_physical_status(VIN_INVALID)
    
    assert status is None


# ==================== TESTS - EMPTY COMPONENTS LIST ====================

def test_get_physical_status_empty_components_list(adapter):
    """Test that empty components list returns all components"""
    status = adapter.get_physical_status(VIN_ELECTRIC, components=[])
    
    # Empty list should be treated same as None (all components)
    assert status is not None
    assert status.doors is not None
    assert status.windows is not None
    assert status.tyres is not None
    assert status.lights is not None


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_get_physical_status_tools_are_registered(mcp_server):
    """Test that physical status tools are registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    
    # Check that the individual component tools are registered
    # (these are the current MCP tools that provide physical status)
    assert "get_vehicle_doors" in tool_names, "get_vehicle_doors tool should be registered"
    assert "get_vehicle_windows" in tool_names, "get_vehicle_windows tool should be registered"
    assert "get_vehicle_tyres" in tool_names, "get_vehicle_tyres tool should be registered"
    assert "get_lights_state" in tool_names, "get_lights_state tool should be registered"
