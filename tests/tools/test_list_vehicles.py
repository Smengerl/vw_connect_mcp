"""
Tests for list_vehicles Tool
=============================

This test suite validates the list_vehicles() adapter method and its MCP tool registration.

What is tested:
- Returns all available vehicles
- Each vehicle contains required fields (VIN, name, model, license_plate)
- Vehicle data accuracy (electric and combustion vehicles)
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
    NAME_COMBUSTION,
    EXPECTED_ELECTRIC_VEHICLE,
    EXPECTED_COMBUSTION_VEHICLE,
)


# ==================== TESTS ====================

def test_list_vehicles_returns_all_vehicles(adapter):
    """Test that list_vehicles returns all available vehicles"""
    vehicles = adapter.list_vehicles()
    
    assert vehicles is not None
    assert len(vehicles) == 2, "Should return exactly 2 test vehicles"


def test_list_vehicles_has_required_fields(adapter):
    """Test that each vehicle has all required fields"""
    vehicles = adapter.list_vehicles()
    
    for vehicle in vehicles:
        assert vehicle.vin is not None
        assert vehicle.name is not None
        assert vehicle.model is not None
        assert vehicle.license_plate is not None


def test_list_vehicles_electric_vehicle_data(adapter):
    """Test that electric vehicle data is correct (also validates presence in list)"""
    vehicles = adapter.list_vehicles()
    
    electric = next((v for v in vehicles if v.vin == VIN_ELECTRIC), None)
    assert electric is not None, "Electric vehicle should be in list"
    assert electric.name == EXPECTED_ELECTRIC_VEHICLE["name"]
    assert electric.model == EXPECTED_ELECTRIC_VEHICLE["model"]
    assert electric.license_plate == EXPECTED_ELECTRIC_VEHICLE["license_plate"]


def test_list_vehicles_combustion_vehicle_data(adapter):
    """Test that combustion vehicle data is correct (also validates presence in list)"""
    vehicles = adapter.list_vehicles()
    
    combustion = next((v for v in vehicles if v.vin == VIN_COMBUSTION), None)
    assert combustion is not None, "Combustion vehicle should be in list"
    assert combustion.name == EXPECTED_COMBUSTION_VEHICLE["name"]
    assert combustion.model == EXPECTED_COMBUSTION_VEHICLE["model"]
    assert combustion.license_plate == EXPECTED_COMBUSTION_VEHICLE["license_plate"]


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_list_vehicles_tool_is_registered(mcp_server):
    """Test that list_vehicles tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "list_vehicles" in tool_names, "list_vehicles tool should be registered in MCP server"
