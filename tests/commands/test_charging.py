"""
Tests for Charging Commands
============================

This test suite validates the start_charging() and stop_charging() adapter methods 
and their MCP tool registration.

What is tested:
- Start charging command execution
- Stop charging command execution
- Vehicle identifier resolution (VIN, name, license plate)
- Invalid vehicle handling
- MCP server tool registration

Note:
- Charging commands are primarily for electric/hybrid vehicles
- TestAdapter allows testing on both vehicle types for robustness

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


# ==================== TESTS - START CHARGING ====================

def test_start_charging_by_vin(adapter):
    """Test starting charging by VIN"""
    result = adapter.execute_command(VIN_ELECTRIC, "start_charging")
    
    assert result is not None
    assert result["success"] is True
    assert "start_charging" in result["message"].lower()


def test_start_charging_by_name(adapter):
    """Test starting charging by name"""
    result = adapter.execute_command(NAME_ELECTRIC, "start_charging")
    
    assert result is not None
    assert result["success"] is True


def test_start_charging_invalid_vehicle(adapter):
    """Test starting charging on non-existent vehicle returns error"""
    result = adapter.execute_command(VIN_INVALID, "start_charging")
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_start_charging_all_identifiers(adapter, identifier):
    """Test that start charging works with VIN, name, or license plate"""
    result = adapter.execute_command(identifier, "start_charging")
    
    assert result is not None
    assert result["success"] is True


# ==================== TESTS - STOP CHARGING ====================

def test_stop_charging_by_vin(adapter):
    """Test stopping charging by VIN"""
    result = adapter.execute_command(VIN_ELECTRIC, "stop_charging")
    
    assert result is not None
    assert result["success"] is True
    assert "stop_charging" in result["message"].lower()


def test_stop_charging_by_name(adapter):
    """Test stopping charging by name"""
    result = adapter.execute_command(NAME_ELECTRIC, "stop_charging")
    
    assert result is not None
    assert result["success"] is True


def test_stop_charging_invalid_vehicle(adapter):
    """Test stopping charging on non-existent vehicle returns error"""
    result = adapter.execute_command(VIN_INVALID, "stop_charging")
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


# ==================== TESTS - ELECTRIC VEHICLE FOCUS ====================

def test_start_charging_electric_vehicle(adapter):
    """Test start charging command on electric vehicle (primary use case)"""
    result = adapter.execute_command(VIN_ELECTRIC, "start_charging")
    
    assert result is not None
    assert result["success"] is True


def test_stop_charging_electric_vehicle(adapter):
    """Test stop charging command on electric vehicle (primary use case)"""
    result = adapter.execute_command(VIN_ELECTRIC, "stop_charging")
    
    assert result is not None
    assert result["success"] is True


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_start_charging_tool_is_registered(mcp_server):
    """Test that start_charging tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "start_charging" in tool_names, "start_charging tool should be registered in MCP server"


@pytest.mark.asyncio
async def test_stop_charging_tool_is_registered(mcp_server):
    """Test that stop_charging tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "stop_charging" in tool_names, "stop_charging tool should be registered in MCP server"
