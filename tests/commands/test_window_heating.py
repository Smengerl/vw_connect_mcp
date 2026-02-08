"""
Tests for Window Heating Commands
==================================

This test suite validates the start_window_heating() and stop_window_heating() adapter methods 
and their MCP tool registration.

What is tested:
- Start window heating command execution
- Stop window heating command execution
- Vehicle identifier resolution (VIN, name, license plate)
- Invalid vehicle handling
- MCP server tool registration

Test data:
- Uses TestAdapter with 2 mock vehicles (ID.7 Tourer electric, Transporter 7 combustion)
- Expected values from tests.test_data module
"""
import pytest
from test_data import (
    VIN_ELECTRIC,
    VIN_COMBUSTION,
    NAME_ELECTRIC,
    LICENSE_PLATE_ELECTRIC,
    VIN_INVALID,
    get_electric_vehicle_identifiers,
)


# ==================== TESTS - START WINDOW HEATING ====================

def test_start_window_heating_by_vin(adapter):
    """Test starting window heating by VIN"""
    result = adapter.start_window_heating(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True
    assert "window" in result["message"].lower() or "heating" in result["message"].lower()


def test_start_window_heating_by_name(adapter):
    """Test starting window heating by name"""
    result = adapter.start_window_heating(NAME_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_start_window_heating_invalid_vehicle(adapter):
    """Test starting window heating on non-existent vehicle returns error"""
    result = adapter.start_window_heating(VIN_INVALID)
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_start_window_heating_all_identifiers(adapter, identifier):
    """Test that start window heating works with VIN, name, or license plate"""
    result = adapter.start_window_heating(identifier)
    
    assert result is not None
    assert result["success"] is True


# ==================== TESTS - STOP WINDOW HEATING ====================

def test_stop_window_heating_by_vin(adapter):
    """Test stopping window heating by VIN"""
    result = adapter.stop_window_heating(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True
    assert "window" in result["message"].lower() or "heating" in result["message"].lower()


def test_stop_window_heating_by_name(adapter):
    """Test stopping window heating by name"""
    result = adapter.stop_window_heating(NAME_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_stop_window_heating_invalid_vehicle(adapter):
    """Test stopping window heating on non-existent vehicle returns error"""
    result = adapter.stop_window_heating(VIN_INVALID)
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


# ==================== TESTS - BOTH VEHICLE TYPES ====================

def test_start_window_heating_electric_vehicle(adapter):
    """Test start window heating command on electric vehicle"""
    result = adapter.start_window_heating(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_start_window_heating_combustion_vehicle(adapter):
    """Test start window heating command on combustion vehicle"""
    result = adapter.start_window_heating(VIN_COMBUSTION)
    
    assert result is not None
    assert result["success"] is True


def test_stop_window_heating_electric_vehicle(adapter):
    """Test stop window heating command on electric vehicle"""
    result = adapter.stop_window_heating(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_stop_window_heating_combustion_vehicle(adapter):
    """Test stop window heating command on combustion vehicle"""
    result = adapter.stop_window_heating(VIN_COMBUSTION)
    
    assert result is not None
    assert result["success"] is True


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_start_window_heating_tool_is_registered(mcp_server):
    """Test that start_window_heating tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "start_window_heating" in tool_names, "start_window_heating tool should be registered in MCP server"


@pytest.mark.asyncio
async def test_stop_window_heating_tool_is_registered(mcp_server):
    """Test that stop_window_heating tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "stop_window_heating" in tool_names, "stop_window_heating tool should be registered in MCP server"
