"""
Tests for vehicle_state Resource
=================================

This test suite validates the data://state/{vehicle_id} MCP resource template implementation.

What is tested:
- Resource template registration in MCP server
- Resource data retrieval via MCP client
- Vehicle identifier resolution (VIN, name, license plate)
- JSON parsing and VehicleModel deserialization
- Data consistency with TestAdapter
- Invalid vehicle handling

Resource tested:
- data://state/{vehicle_id}: Returns complete vehicle state for given identifier

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
    LICENSE_PLATE_ELECTRIC,
    VIN_INVALID,
    EXPECTED_ELECTRIC_VEHICLE,
    EXPECTED_COMBUSTION_VEHICLE,
    get_electric_vehicle_identifiers,
)
from weconnect_mcp.adapter.carconnectivity_adapter import VehicleModel

import logging
logger = logging.getLogger(__name__)


# ==================== TESTS - RESOURCE REGISTRATION ====================

@pytest.mark.asyncio
async def test_vehicle_state_resource_template_is_registered(mcp_server):
    """Test that data://state/{vehicle_id} resource template is registered"""
    all_resource_templates = await mcp_server.get_resource_templates()
    
    assert all_resource_templates is not None, "Resource templates should not be None"
    template_uris = list(all_resource_templates.keys())
    logger.debug(f"Registered resource templates: {template_uris}")
    assert "data://state/{vehicle_id}" in template_uris, "data://state/{vehicle_id} template should be registered"


# ==================== TESTS - RESOURCE DATA RETRIEVAL ====================

@pytest.mark.asyncio
async def test_vehicle_state_resource_by_vin(mcp_server):
    """Test that resource template returns data for valid VIN"""
    state_resource_template = await mcp_server.get_resource_template("data://state/{vehicle_id}")
    
    assert state_resource_template is not None, "Resource template should not be None"
    
    # Read state for electric vehicle by VIN
    vehicle_state = await state_resource_template.read({"vehicle_id": VIN_ELECTRIC})
    
    assert vehicle_state is not None, "Vehicle state should not be None"
    assert isinstance(vehicle_state, VehicleModel), "State should be VehicleModel instance"
    assert vehicle_state.vin == VIN_ELECTRIC


@pytest.mark.asyncio
async def test_vehicle_state_resource_via_client_by_vin(mcp_client):
    """Test that MCP client can read vehicle state by VIN"""
    result = await mcp_client.read_resource(f"data://state/{VIN_ELECTRIC}")
    logger.debug(f"Client resource read result: {result}")
    
    assert result is not None, "Result should not be None"
    assert len(result) == 1, f"Expected 1 result, got {len(result)}"
    assert hasattr(result[0], "text"), "Result[0] should have 'text' attribute"
    
    # Parse JSON to VehicleModel
    vehicle_str = result[0].text
    vehicle = VehicleModel.model_validate_json(vehicle_str)
    
    assert vehicle.vin == VIN_ELECTRIC
    assert vehicle.name == EXPECTED_ELECTRIC_VEHICLE["name"]


@pytest.mark.asyncio
async def test_vehicle_state_resource_via_client_by_name(mcp_client):
    """Test that MCP client can read vehicle state by name"""
    result = await mcp_client.read_resource(f"data://state/{NAME_ELECTRIC}")
    
    assert result is not None
    vehicle = VehicleModel.model_validate_json(result[0].text)
    
    assert vehicle.vin == VIN_ELECTRIC
    assert vehicle.name == NAME_ELECTRIC


@pytest.mark.asyncio
async def test_vehicle_state_resource_via_client_by_license_plate(mcp_client):
    """Test that MCP client can read vehicle state by license plate"""
    result = await mcp_client.read_resource(f"data://state/{LICENSE_PLATE_ELECTRIC}")
    
    assert result is not None
    vehicle = VehicleModel.model_validate_json(result[0].text)
    
    # Verify it's the correct vehicle (by VIN since license_plate might not be in VehicleModel)
    assert vehicle.vin == VIN_ELECTRIC


@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
@pytest.mark.asyncio
async def test_vehicle_state_resource_all_identifiers(mcp_client, identifier):
    """Test that resource works with VIN, name, or license plate"""
    result = await mcp_client.read_resource(f"data://state/{identifier}")
    
    assert result is not None
    vehicle = VehicleModel.model_validate_json(result[0].text)
    assert vehicle.vin == VIN_ELECTRIC


# ==================== TESTS - DATA STRUCTURE ====================

@pytest.mark.asyncio
async def test_vehicle_state_resource_electric_vehicle_fields(mcp_client):
    """Test that electric vehicle state has all expected fields"""
    result = await mcp_client.read_resource(f"data://state/{VIN_ELECTRIC}")
    vehicle = VehicleModel.model_validate_json(result[0].text)
    
    # Basic fields
    assert vehicle.vin == EXPECTED_ELECTRIC_VEHICLE["vin"]
    assert vehicle.name == EXPECTED_ELECTRIC_VEHICLE["name"]
    assert vehicle.model == EXPECTED_ELECTRIC_VEHICLE["model"]
    assert vehicle.manufacturer == EXPECTED_ELECTRIC_VEHICLE["manufacturer"]
    assert vehicle.type == EXPECTED_ELECTRIC_VEHICLE["type"]
    
    # State should be present
    assert vehicle.state is not None
    assert vehicle.connection_state is not None


@pytest.mark.asyncio
async def test_vehicle_state_resource_combustion_vehicle_fields(mcp_client):
    """Test that combustion vehicle state has all expected fields"""
    result = await mcp_client.read_resource(f"data://state/{VIN_COMBUSTION}")
    vehicle = VehicleModel.model_validate_json(result[0].text)
    
    # Basic fields
    assert vehicle.vin == EXPECTED_COMBUSTION_VEHICLE["vin"]
    assert vehicle.name == EXPECTED_COMBUSTION_VEHICLE["name"]
    assert vehicle.model == EXPECTED_COMBUSTION_VEHICLE["model"]
    assert vehicle.type == EXPECTED_COMBUSTION_VEHICLE["type"]


# ==================== TESTS - BOTH VEHICLE TYPES ====================

@pytest.mark.parametrize("vin,expected", [
    (VIN_ELECTRIC, EXPECTED_ELECTRIC_VEHICLE),
    (VIN_COMBUSTION, EXPECTED_COMBUSTION_VEHICLE),
])
@pytest.mark.asyncio
async def test_vehicle_state_resource_both_vehicles(mcp_client, vin, expected):
    """Test that resource returns correct data for both vehicle types"""
    result = await mcp_client.read_resource(f"data://state/{vin}")
    vehicle = VehicleModel.model_validate_json(result[0].text)
    
    assert vehicle.vin == expected["vin"]
    assert vehicle.name == expected["name"]
    assert vehicle.model == expected["model"]
    assert vehicle.type == expected["type"]


# ==================== TESTS - DATA CONSISTENCY ====================

@pytest.mark.asyncio
async def test_vehicle_state_resource_matches_adapter(adapter, mcp_client):
    """Test that resource data matches adapter get_vehicle() output"""
    # Get data from adapter
    adapter_vehicle = adapter.get_vehicle(VIN_ELECTRIC)
    
    # Get data from resource
    result = await mcp_client.read_resource(f"data://state/{VIN_ELECTRIC}")
    resource_vehicle = VehicleModel.model_validate_json(result[0].text)
    
    # Compare
    assert resource_vehicle == adapter_vehicle, "Resource data should match adapter data"


@pytest.mark.asyncio
async def test_vehicle_state_resource_matches_adapter_for_both_vehicles(adapter, mcp_client):
    """Test that resource matches adapter for both test vehicles"""
    for vin in [VIN_ELECTRIC, VIN_COMBUSTION]:
        # Get data from adapter
        adapter_vehicle = adapter.get_vehicle(vin)
        
        # Get data from resource
        result = await mcp_client.read_resource(f"data://state/{vin}")
        resource_vehicle = VehicleModel.model_validate_json(result[0].text)
        
        # Compare
        assert resource_vehicle == adapter_vehicle, f"Resource data should match adapter for {vin}"


# ==================== TESTS - ERROR HANDLING ====================

@pytest.mark.asyncio
async def test_vehicle_state_resource_invalid_vehicle_returns_none(mcp_server):
    """Test that resource returns None for non-existent vehicle"""
    state_resource_template = await mcp_server.get_resource_template("data://state/{vehicle_id}")
    
    vehicle_state = await state_resource_template.read({"vehicle_id": VIN_INVALID})
    
    # Should return None for non-existent vehicle
    assert vehicle_state is None, "Should return None for invalid vehicle"
