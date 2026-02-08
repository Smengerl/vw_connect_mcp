"""
Tests for Lock/Unlock Commands
===============================

This test suite validates the lock_vehicle() and unlock_vehicle() adapter methods 
and their MCP tool registration.

What is tested:
- Lock command execution success
- Unlock command execution success
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


# ==================== TESTS - LOCK COMMAND ====================

def test_lock_vehicle_by_vin(adapter):
    """Test locking vehicle by VIN"""
    result = adapter.lock_vehicle(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True
    assert "lock" in result["message"].lower()


def test_lock_vehicle_by_name(adapter):
    """Test locking vehicle by name"""
    result = adapter.lock_vehicle(NAME_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_lock_vehicle_invalid_vehicle(adapter):
    """Test locking non-existent vehicle returns error"""
    result = adapter.lock_vehicle(VIN_INVALID)
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_lock_vehicle_all_identifiers(adapter, identifier):
    """Test that lock works with VIN, name, or license plate"""
    result = adapter.lock_vehicle(identifier)
    
    assert result is not None
    assert result["success"] is True


# ==================== TESTS - UNLOCK COMMAND ====================

def test_unlock_vehicle_by_vin(adapter):
    """Test unlocking vehicle by VIN"""
    result = adapter.unlock_vehicle(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True
    assert "unlock" in result["message"].lower()


def test_unlock_vehicle_by_name(adapter):
    """Test unlocking vehicle by name"""
    result = adapter.unlock_vehicle(NAME_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_unlock_vehicle_invalid_vehicle(adapter):
    """Test unlocking non-existent vehicle returns error"""
    result = adapter.unlock_vehicle(VIN_INVALID)
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


# ==================== TESTS - BOTH VEHICLE TYPES ====================

def test_lock_electric_vehicle(adapter):
    """Test lock command on electric vehicle"""
    result = adapter.lock_vehicle(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_lock_combustion_vehicle(adapter):
    """Test lock command on combustion vehicle"""
    result = adapter.lock_vehicle(VIN_COMBUSTION)
    
    assert result is not None
    assert result["success"] is True


def test_unlock_electric_vehicle(adapter):
    """Test unlock command on electric vehicle"""
    result = adapter.unlock_vehicle(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_unlock_combustion_vehicle(adapter):
    """Test unlock command on combustion vehicle"""
    result = adapter.unlock_vehicle(VIN_COMBUSTION)
    
    assert result is not None
    assert result["success"] is True


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_lock_vehicle_tool_is_registered(mcp_server):
    """Test that lock_vehicle tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "lock_vehicle" in tool_names, "lock_vehicle tool should be registered in MCP server"


@pytest.mark.asyncio
async def test_unlock_vehicle_tool_is_registered(mcp_server):
    """Test that unlock_vehicle tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "unlock_vehicle" in tool_names, "unlock_vehicle tool should be registered in MCP server"
