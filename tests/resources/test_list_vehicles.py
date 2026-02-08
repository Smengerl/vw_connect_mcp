"""
Tests for list_vehicles Resource
=================================

This test suite validates the data://list_vehicles MCP resource implementation.

What is tested:
- Resource registration in MCP server
- Resource data retrieval via MCP client
- JSON parsing and deserialization
- Vehicle list completeness (2 mock vehicles)
- Vehicle data structure (VIN, name, model, license_plate)
- Data consistency with TestAdapter

Resource tested:
- data://list_vehicles: Returns list of all available vehicles

Test data:
- Uses TestAdapter with 2 mock vehicles (ID.7 Tourer electric, Transporter 7 combustion)
- Expected values from tests.test_data module
"""
import pytest
import json
from test_data import (
    VIN_ELECTRIC,
    VIN_COMBUSTION,
    NAME_ELECTRIC,
    NAME_COMBUSTION,
    EXPECTED_ELECTRIC_VEHICLE,
    EXPECTED_COMBUSTION_VEHICLE,
)

import logging
logger = logging.getLogger(__name__)


# ==================== TESTS - RESOURCE REGISTRATION ====================

@pytest.mark.asyncio
async def test_list_vehicles_resource_is_registered(mcp_server):
    """Test that data://vehicles resource is registered in the MCP server"""
    all_resources = await mcp_server.get_resources()
    
    assert all_resources is not None, "Resources should not be None"
    resource_uris = list(all_resources.keys())
    logger.debug(f"Registered resources: {resource_uris}")
    assert "data://vehicles" in resource_uris, "data://vehicles resource should be registered"


# ==================== TESTS - RESOURCE DATA RETRIEVAL ====================

@pytest.mark.asyncio
async def test_list_vehicles_resource_returns_data(mcp_server):
    """Test that data://vehicles resource returns valid data"""
    vehicles_resource = await mcp_server.get_resource("data://vehicles")
    
    assert vehicles_resource is not None, "Vehicle resource should not be None"
    
    # Read resource data
    vehicles_str = await vehicles_resource.read()
    assert vehicles_str is not None, "Resource data should not be None"
    
    # Parse JSON
    vehicles = json.loads(vehicles_str)
    assert isinstance(vehicles, list), "Resource data should be a list"
    assert len(vehicles) == 2, "Should return exactly 2 test vehicles"


@pytest.mark.asyncio
async def test_list_vehicles_resource_via_client(mcp_client):
    """Test that MCP client can read data://vehicles resource"""
    result = await mcp_client.read_resource("data://vehicles")
    logger.debug(f"Client resource read result: {result}")
    
    assert result is not None, "Result should not be None"
    assert len(result) == 1, f"Expected 1 result, got {len(result)}"
    assert hasattr(result[0], "text"), "Result[0] should have 'text' attribute"
    
    # Parse JSON from text
    vehicles_str = result[0].text
    vehicles = json.loads(vehicles_str)
    
    assert isinstance(vehicles, list), "Vehicles should be a list"
    assert len(vehicles) == 2, "Should return 2 vehicles"


# ==================== TESTS - DATA STRUCTURE ====================

@pytest.mark.asyncio
async def test_list_vehicles_resource_has_required_fields(mcp_client):
    """Test that each vehicle in resource has all required fields"""
    result = await mcp_client.read_resource("data://vehicles")
    vehicles = json.loads(result[0].text)
    
    for vehicle in vehicles:
        assert isinstance(vehicle, dict), "Vehicle should be a dict"
        assert "vin" in vehicle, "Vehicle should have 'vin' field"
        assert "name" in vehicle, "Vehicle should have 'name' field"
        assert "model" in vehicle, "Vehicle should have 'model' field"
        assert "license_plate" in vehicle, "Vehicle should have 'license_plate' field"


@pytest.mark.asyncio
async def test_list_vehicles_resource_electric_vehicle_data(mcp_client):
    """Test that electric vehicle data in resource is correct"""
    result = await mcp_client.read_resource("data://vehicles")
    vehicles = json.loads(result[0].text)
    
    electric = next((v for v in vehicles if v["vin"] == VIN_ELECTRIC), None)
    assert electric is not None, "Electric vehicle should be in resource"
    assert electric["name"] == EXPECTED_ELECTRIC_VEHICLE["name"]
    assert electric["model"] == EXPECTED_ELECTRIC_VEHICLE["model"]
    assert electric["license_plate"] == EXPECTED_ELECTRIC_VEHICLE["license_plate"]


@pytest.mark.asyncio
async def test_list_vehicles_resource_combustion_vehicle_data(mcp_client):
    """Test that combustion vehicle data in resource is correct"""
    result = await mcp_client.read_resource("data://vehicles")
    vehicles = json.loads(result[0].text)
    
    combustion = next((v for v in vehicles if v["vin"] == VIN_COMBUSTION), None)
    assert combustion is not None, "Combustion vehicle should be in resource"
    assert combustion["name"] == EXPECTED_COMBUSTION_VEHICLE["name"]
    assert combustion["model"] == EXPECTED_COMBUSTION_VEHICLE["model"]
    assert combustion["license_plate"] == EXPECTED_COMBUSTION_VEHICLE["license_plate"]


# ==================== TESTS - DATA CONSISTENCY ====================

@pytest.mark.asyncio
async def test_list_vehicles_resource_matches_adapter(adapter, mcp_client):
    """Test that resource data matches adapter list_vehicles() output"""
    # Get data from adapter
    adapter_vehicles = adapter.list_vehicles()
    
    # Get data from resource
    result = await mcp_client.read_resource("data://vehicles")
    resource_vehicles = json.loads(result[0].text)
    
    # Compare counts
    assert len(resource_vehicles) == len(adapter_vehicles), "Resource should return same count as adapter"
    
    # Compare VINs
    resource_vins = {v["vin"] for v in resource_vehicles}
    adapter_vins = {v.vin for v in adapter_vehicles}
    assert resource_vins == adapter_vins, "Resource VINs should match adapter VINs"
