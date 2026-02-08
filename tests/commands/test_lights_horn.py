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
    result = adapter.flash_lights(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True
    assert "flash" in result["message"].lower()


def test_flash_lights_by_name(adapter):
    """Test flashing lights by name"""
    result = adapter.flash_lights(NAME_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_flash_lights_with_duration(adapter):
    """Test flashing lights with duration parameter"""
    result = adapter.flash_lights(VIN_ELECTRIC, duration_seconds=5)
    
    assert result is not None
    assert result["success"] is True
    assert "5 seconds" in result["message"]


def test_flash_lights_invalid_vehicle(adapter):
    """Test flashing lights on non-existent vehicle returns error"""
    result = adapter.flash_lights(VIN_INVALID)
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_flash_lights_all_identifiers(adapter, identifier):
    """Test that flash works with VIN, name, or license plate"""
    result = adapter.flash_lights(identifier)
    
    assert result is not None
    assert result["success"] is True


# ==================== TESTS - HONK AND FLASH ====================

def test_honk_and_flash_by_vin(adapter):
    """Test honk and flash by VIN"""
    result = adapter.honk_and_flash(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True
    assert "honk" in result["message"].lower() or "flash" in result["message"].lower()


def test_honk_and_flash_by_name(adapter):
    """Test honk and flash by name"""
    result = adapter.honk_and_flash(NAME_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_honk_and_flash_with_duration(adapter):
    """Test honk and flash with duration parameter"""
    result = adapter.honk_and_flash(VIN_ELECTRIC, duration_seconds=10)
    
    assert result is not None
    assert result["success"] is True
    assert "10 seconds" in result["message"]


def test_honk_and_flash_invalid_vehicle(adapter):
    """Test honk and flash on non-existent vehicle returns error"""
    result = adapter.honk_and_flash(VIN_INVALID)
    
    assert result is not None
    assert result["success"] is False
    assert "error" in result


# ==================== TESTS - BOTH VEHICLE TYPES ====================

def test_flash_lights_electric_vehicle(adapter):
    """Test flash lights command on electric vehicle"""
    result = adapter.flash_lights(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_flash_lights_combustion_vehicle(adapter):
    """Test flash lights command on combustion vehicle"""
    result = adapter.flash_lights(VIN_COMBUSTION)
    
    assert result is not None
    assert result["success"] is True


def test_honk_and_flash_electric_vehicle(adapter):
    """Test honk and flash command on electric vehicle"""
    result = adapter.honk_and_flash(VIN_ELECTRIC)
    
    assert result is not None
    assert result["success"] is True


def test_honk_and_flash_combustion_vehicle(adapter):
    """Test honk and flash command on combustion vehicle"""
    result = adapter.honk_and_flash(VIN_COMBUSTION)
    
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
