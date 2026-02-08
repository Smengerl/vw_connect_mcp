"""
Tests for Climatization Commands
=================================

This test suite validates the start_climatization() and stop_climatization() adapter methods 
and their MCP tool registration.

What is tested:
- Start climatization command execution
- Stop climatization command execution
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


# ==================== TESTS - START CLIMATIZATION ====================

def test_start_climatization_by_vin(adapter):
    """Test starting climatization by VIN"""
    result = adapter.execute_command(VIN_ELECTRIC, "start_climatization")
    
    assert result is not None
    assert result["success"] is True
    assert "start_climatization" in result["message"].lower()


def test_start_climatization_by_name(adapter):
    """Test starting climatization by name"""
    result = adapter.execute_command(NAME_ELECTRIC, "start_climatization")
    
    assert result is not None
    assert result["success"] is True


def test_start_climatization_invalid_vehicle(adapter):
    """Test starting climatization on non-existent vehicle returns error"""
    result = adapter.execute_command(VIN_INVALID, "start_climatization")
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_start_climatization_all_identifiers(adapter, identifier):
    """Test that start climatization works with VIN, name, or license plate"""
    result = adapter.execute_command(identifier, "start_climatization")
    
    assert result is not None
    assert result["success"] is True


# ==================== TESTS - STOP CLIMATIZATION ====================

def test_stop_climatization_by_vin(adapter):
    """Test stopping climatization by VIN"""
    result = adapter.execute_command(VIN_ELECTRIC, "stop_climatization")
    
    assert result is not None
    assert result["success"] is True
    assert "stop_climatization" in result["message"].lower()


def test_stop_climatization_by_name(adapter):
    """Test stopping climatization by name"""
    result = adapter.execute_command(NAME_ELECTRIC, "stop_climatization")
    
    assert result is not None
    assert result["success"] is True


def test_stop_climatization_invalid_vehicle(adapter):
    """Test stopping climatization on non-existent vehicle returns error"""
    result = adapter.execute_command(VIN_INVALID, "stop_climatization")
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


# ==================== TESTS - BOTH VEHICLE TYPES ====================

def test_start_climatization_electric_vehicle(adapter):
    """Test start climatization command on electric vehicle"""
    result = adapter.execute_command(VIN_ELECTRIC, "start_climatization")
    
    assert result is not None
    assert result["success"] is True


def test_start_climatization_combustion_vehicle(adapter):
    """Test start climatization command on combustion vehicle"""
    result = adapter.execute_command(VIN_COMBUSTION, "start_climatization")
    
    assert result is not None
    assert result["success"] is True


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_start_climatization_tool_is_registered(mcp_server):
    """Test that start_climatization tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "start_climatization" in tool_names, "start_climatization tool should be registered in MCP server"


@pytest.mark.asyncio
async def test_stop_climatization_tool_is_registered(mcp_server):
    """Test that stop_climatization tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "stop_climatization" in tool_names, "stop_climatization tool should be registered in MCP server"
