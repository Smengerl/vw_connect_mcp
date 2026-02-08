"""
Tests for Light & Horn Commands
================================

This test suite validates the flash_lights() and honk_and_flash() adapter methods 
and their MCP tool registration.

What is tested:
- Flash lights command execution
- Honk and flash command execution
- Optional duration parameter handling
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


# ==================== TESTS - FLASH LIGHTS ====================

def test_flash_lights_by_vin(adapter):
    """Test flashing lights by VIN"""
    result = adapter.execute_command(VIN_ELECTRIC, "flash")
    
    assert result is not None
    assert result["success"] is True
    assert "flash" in result["message"].lower()


def test_flash_lights_by_name(adapter):
    """Test flashing lights by name"""
    result = adapter.execute_command(NAME_ELECTRIC, "flash")
    
    assert result is not None
    assert result["success"] is True


def test_flash_lights_with_duration(adapter):
    """Test flashing lights with duration parameter"""
    result = adapter.execute_command(VIN_ELECTRIC, "flash", duration=5)
    
    assert result is not None
    assert result["success"] is True


def test_flash_lights_invalid_vehicle(adapter):
    """Test flashing lights on non-existent vehicle returns error"""
    result = adapter.execute_command(VIN_INVALID, "flash")
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_flash_lights_all_identifiers(adapter, identifier):
    """Test that flash works with VIN, name, or license plate"""
    result = adapter.execute_command(identifier, "flash")
    
    assert result is not None
    assert result["success"] is True


# ==================== TESTS - HONK AND FLASH ====================

def test_honk_and_flash_by_vin(adapter):
    """Test honk and flash by VIN"""
    result = adapter.execute_command(VIN_ELECTRIC, "honk_and_flash")
    
    assert result is not None
    assert result["success"] is True
    assert "honk_and_flash" in result["message"].lower()


def test_honk_and_flash_by_name(adapter):
    """Test honk and flash by name"""
    result = adapter.execute_command(NAME_ELECTRIC, "honk_and_flash")
    
    assert result is not None
    assert result["success"] is True


def test_honk_and_flash_with_duration(adapter):
    """Test honk and flash with duration parameter"""
    result = adapter.execute_command(VIN_ELECTRIC, "honk_and_flash", duration=10)
    
    assert result is not None
    assert result["success"] is True


def test_honk_and_flash_invalid_vehicle(adapter):
    """Test honk and flash on non-existent vehicle returns error"""
    result = adapter.execute_command(VIN_INVALID, "honk_and_flash")
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


# ==================== TESTS - BOTH VEHICLE TYPES ====================

def test_flash_lights_electric_vehicle(adapter):
    """Test flash lights command on electric vehicle"""
    result = adapter.execute_command(VIN_ELECTRIC, "flash")
    
    assert result is not None
    assert result["success"] is True


def test_flash_lights_combustion_vehicle(adapter):
    """Test flash lights command on combustion vehicle"""
    result = adapter.execute_command(VIN_COMBUSTION, "flash")
    
    assert result is not None
    assert result["success"] is True


def test_honk_and_flash_electric_vehicle(adapter):
    """Test honk and flash command on electric vehicle"""
    result = adapter.execute_command(VIN_ELECTRIC, "honk_and_flash")
    
    assert result is not None
    assert result["success"] is True


def test_honk_and_flash_combustion_vehicle(adapter):
    """Test honk and flash command on combustion vehicle"""
    result = adapter.execute_command(VIN_COMBUSTION, "honk_and_flash")
    
    assert result is not None
    assert result["success"] is True


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_flash_lights_tool_is_registered(mcp_server):
    """Test that flash_lights tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "flash_lights" in tool_names, "flash_lights tool should be registered in MCP server"


@pytest.mark.asyncio
async def test_honk_and_flash_tool_is_registered(mcp_server):
    """Test that honk_and_flash tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "honk_and_flash" in tool_names, "honk_and_flash tool should be registered in MCP server"
