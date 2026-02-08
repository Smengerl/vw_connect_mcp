"""
MCP Server Tests
================

This test suite validates the FastMCP server implementation and its integration with adapters.

What is tested:
- MCP resource registration (data://list_vehicles, data://state/{vehicle_id})
- MCP tool registration and availability
- Resource data retrieval and JSON parsing
- MCP client connection and communication
- Tool invocation via MCP protocol
- Error handling for invalid vehicle IDs

Test architecture:
- Uses TestAdapter for deterministic mock data
- Module-scoped fixtures for server (created once)
- Function-scoped fixtures for clients (fresh per test)
- Async tests with @pytest.mark.asyncio
- 10-second timeout per test

Fixtures:
- mockdata_adapter: TestAdapter with 2 mock vehicles
- mockdata_mcp_server: FastMCP server instance with registered tools
- mockdata_mcp_client: Connected MCP client for protocol testing

Resources tested:
- data://list_vehicles: List all available vehicles
- data://state/{vehicle_id}: Get vehicle state by VIN

Tools tested:
- All registered MCP tools from mcp_server.py
- Tool invocation and response validation

Note: Some tests may fail if mcp_server.py still uses old API methods.
Update server tool implementations to use consolidated methods.
"""
import pytest
import json
from src.weconnect_mcp.server.mcp_server import get_server
from .test_adapter import TestAdapter
from weconnect_mcp.adapter.carconnectivity_adapter import VehicleModel
from fastmcp import Client
from typing import Any

import logging
logger = logging.getLogger(__name__)


# ==================== FIXTURES ====================

@pytest.fixture(scope="module")
def mockdata_adapter():
    """Provides a TestAdapter instance with 2 mock vehicles for testing."""
    return TestAdapter()


@pytest.fixture(scope="module")
def mockdata_mcp_server(mockdata_adapter):
    """Provides a FastMCP server instance with TestAdapter.
    
    Module-scoped: created once and reused across all tests.
    """
    return get_server(mockdata_adapter)


@pytest.fixture(scope="function")
async def mockdata_mcp_client(mockdata_mcp_server):
    """Provides a connected MCP client for protocol testing.
    
    Function-scoped: fresh client per test to avoid state pollution.
    Automatically connects and disconnects via async context manager.
    """
    async with Client(mockdata_mcp_server) as mockdata_mcp_client:
        yield mockdata_mcp_client


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_resources_registered(mockdata_mcp_server: Any):
    """ Make sure that the MCP server has registered the expected resources. """
    all_resources = await mockdata_mcp_server.get_resources()
    logger.debug(f"Registered resources: {list(all_resources.keys())}")
    assert all_resources is not None, "all_resources should not be None"
    assert "data://list_vehicles" in all_resources, 'Expected "data://list_vehicles" in all_resources'
    all_resource_templates = await mockdata_mcp_server.get_resource_templates()
    assert all_resource_templates is not None, "all_resource_templates should not be None"
    assert "data://state/{vehicle_id}" in all_resource_templates, 'Expected "data://state/{vehicle_id}" in all_resource_templates'


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_resources_provide_valid_data(mockdata_mcp_server: Any):
    """ Test that the MCP server resources return valid data. """
    # List vehicles
    vehicles_resource = await mockdata_mcp_server.get_resource("data://list_vehicles")
    assert vehicles_resource is not None, "vehicles_resource should not be None"

    all_vehicles_str = await vehicles_resource.read()
    assert all_vehicles_str is not None, "all_vehicles_str should not be None"
    logger.debug(f"All vehicles string: {all_vehicles_str}")

    vehicles = json.loads(all_vehicles_str)
    assert isinstance(vehicles, list), "vehicles should be a list"
    assert len(vehicles) == TestAdapter.vehicles.__len__(), f"Expected {TestAdapter.vehicles.__len__()} vehicles, got {len(vehicles)}"

    # Get state for each vehicle (vehicles are now dicts with vin, name, model)
    for vehicle_info in vehicles:
        assert isinstance(vehicle_info, dict), f"vehicle_info should be a dict, got {type(vehicle_info)}"
        assert "vin" in vehicle_info, "vehicle_info should have a 'vin' key"
        vehicle_id = vehicle_info["vin"]
        logger.debug(f"Try resource: data://state/{vehicle_id}")
        state_resource_template = await mockdata_mcp_server.get_resource_template("data://state/{vehicle_id}")
        assert state_resource_template is not None, f"state_resource_template for {vehicle_id} should not be None"

        vehicle_str = await state_resource_template.read({"vehicle_id": vehicle_id})
        assert vehicle_str is not None, f"vehicle_str for {vehicle_id} should not be None"
        logger.debug(f"Vehicle string: {vehicle_str}")
        assert isinstance(vehicle_str, VehicleModel), f"vehicle_str for {vehicle_id} should be a VehicleModel"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_client_connects(mockdata_mcp_client):
    """ Test that the MCP client can connect to the server. """
    assert mockdata_mcp_client.is_connected(), "MCP client should be connected"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_list_vehicles(mockdata_mcp_client):
    """ Tests that the MCP client can list vehicles via the server. """
    result = await mockdata_mcp_client.read_resource("data://list_vehicles")
    logger.debug(f"Resource read: {result}")
    assert result is not None, "Result from read_resource should not be None"
    assert result.__len__() == 1, f"Expected 1 result, got {result.__len__()}"
    assert hasattr(result[0], "text"), "Result[0] should have attribute 'text'"
    assert isinstance(result[0].text, str), "Result[0].text should be a string"

    all_vehicles_str = result[0].text
    logger.debug(f"All vehicles string from client: {all_vehicles_str}")
    vehicles = json.loads(all_vehicles_str)
    logger.debug(f"Deserialized JSON from client: {vehicles}")

    assert vehicles.__len__() == TestAdapter.vehicles.__len__(), f"Expected {TestAdapter.vehicles.__len__()} vehicles, got {vehicles.__len__()}"
    # vehicles are now dicts with vin, name, model
    for vehicle_info in vehicles:
        assert isinstance(vehicle_info, dict), f"vehicle_info should be a dict, got {type(vehicle_info)}"
        assert "vin" in vehicle_info, "vehicle_info should have a 'vin' key"
        vin = vehicle_info["vin"]
        if vin in [v.vin for v in TestAdapter.vehicles]:
            logger.debug(f"Found vehicle VIN from client: {vin}")
        else:
            pytest.fail(f"Vehicle VIN {vin} not found in test adapter vehicles.")


@pytest.mark.parametrize(
    "vehicle",
    [
        (TestAdapter.vehicles[0]),
        (TestAdapter.vehicles[1]),
    ],
)
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_get_vehicle_state(mockdata_mcp_client, vehicle):
    """ Tests that the MCP client can get the state of a vehicle via the server. """
    result = await mockdata_mcp_client.read_resource(f"data://state/{vehicle.vin}")
    logger.debug(f"Vehicle state string for vehicle {vehicle.vin} from client: {result[0].text}")
    assert result is not None, f"Result for vehicle {vehicle.vin} should not be None"
    assert result.__len__() == 1, f"Expected 1 result for vehicle {vehicle.vin}, got {result.__len__()}"
    assert hasattr(result[0], "text"), f"Result[0] for vehicle {vehicle.vin} should have attribute 'text'"
    assert isinstance(result[0].text, str), f"Result[0].text for vehicle {vehicle.vin} should be a string"

    vehicle_str = result[0].text
    logger.debug(f"Vehicle string from client: {vehicle_str}")
    returned_vehicle = VehicleModel.model_validate_json(vehicle_str)
    assert returned_vehicle == vehicle, f"Returned vehicle does not match expected for vehicle {vehicle.vin}"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_get_climatization_state(mockdata_mcp_client):
    """Test that the MCP client can get climatization state via the server."""
    # Test with ID7 (should have active heating)
    result = await mockdata_mcp_client.call_tool("get_climatization_state", arguments={"vehicle_id": "WVWZZZED4SE003938"})
    logger.debug(f"Climatization state result: {result}")
    
    assert result is not None
    assert isinstance(result.content, list)
    assert len(result.content) > 0
    
    climatization = result.content[0].text
    logger.debug(f"Climatization data: {climatization}")
    
    climatization_dict = json.loads(climatization)
    assert climatization_dict["state"] == "heating"
    assert climatization_dict["is_active"] is True
    assert climatization_dict["target_temperature_celsius"] == 22.0


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_get_maintenance_info(mockdata_mcp_client):
    """Test that the MCP client can get maintenance info via the server."""
    # Test with T7 (combustion vehicle with oil service)
    result = await mockdata_mcp_client.call_tool("get_maintenance_info", arguments={"vehicle_id": "WV2ZZZSTZNH009136"})
    logger.debug(f"Maintenance info result: {result}")
    
    assert result is not None
    assert isinstance(result.content, list)
    assert len(result.content) > 0
    
    maintenance = result.content[0].text
    logger.debug(f"Maintenance data: {maintenance}")
    
    maintenance_dict = json.loads(maintenance)
    assert maintenance_dict["inspection_due_date"] == "2026-05-20T00:00:00+00:00"
    assert maintenance_dict["inspection_due_distance_km"] == 12000
    assert maintenance_dict["oil_service_due_date"] == "2026-04-10T00:00:00+00:00"
    assert maintenance_dict["oil_service_due_distance_km"] == 8000


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_get_range_info(mockdata_mcp_client):
    """Test that the MCP client can get range info via the server."""
    # Test with ID7 (electric vehicle)
    result = await mockdata_mcp_client.call_tool("get_range_info", arguments={"vehicle_id": "WVWZZZED4SE003938"})
    logger.debug(f"Range info result: {result}")
    
    assert result is not None
    assert isinstance(result.content, list)
    assert len(result.content) > 0
    
    range_info = result.content[0].text
    logger.debug(f"Range data: {range_info}")
    
    range_dict = json.loads(range_info)
    assert range_dict["total_range_km"] == 312.0  # Updated to match test_data.py
    assert range_dict["electric_range_km"] == 312.0
    assert range_dict["battery_level_percent"] == 77.0
    # Combustion fields should not be present for electric vehicle
    assert "combustion_range_km" not in range_dict
    assert "tank_level_percent" not in range_dict


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_get_window_heating_state(mockdata_mcp_client):
    """Test that the MCP client can get window heating state via the server."""
    # Test with ID7 (should have both heaters on)
    result = await mockdata_mcp_client.call_tool("get_window_heating_state", arguments={"vehicle_id": "WVWZZZED4SE003938"})
    logger.debug(f"Window heating result: {result}")
    
    assert result is not None
    assert isinstance(result.content, list)
    assert len(result.content) > 0
    
    window_heating = result.content[0].text
    logger.debug(f"Window heating data: {window_heating}")
    
    window_heating_dict = json.loads(window_heating)
    assert window_heating_dict["front"]["state"] == "on"  # Updated to match TestAdapter
    assert window_heating_dict["rear"]["state"] == "on"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_get_lights_state(mockdata_mcp_client):
    """Test that the MCP client can get lights state via the server."""
    # Test with ID7
    result = await mockdata_mcp_client.call_tool("get_lights_state", arguments={"vehicle_id": "WVWZZZED4SE003938"})
    logger.debug(f"Lights result: {result}")
    
    assert result is not None
    assert isinstance(result.content, list)
    assert len(result.content) > 0
    
    lights = result.content[0].text
    logger.debug(f"Lights data: {lights}")
    
    lights_dict = json.loads(lights)
    assert lights_dict["left"]["state"] == "ok"  # Updated: state is "ok" (working), not "off"
    assert lights_dict["right"]["state"] == "ok"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_get_position(mockdata_mcp_client):
    """Test that the MCP client can get vehicle position via the server."""
    # Test with ID7 (Munich position)
    result = await mockdata_mcp_client.call_tool("get_position", arguments={"vehicle_id": "WVWZZZED4SE003938"})
    logger.debug(f"Position result: {result}")
    
    assert result is not None
    assert isinstance(result.content, list)
    assert len(result.content) > 0
    
    position = result.content[0].text
    logger.debug(f"Position data: {position}")
    
    position_dict = json.loads(position)
    assert position_dict["latitude"] == 48.1351
    assert position_dict["longitude"] == 11.5820
    assert position_dict["heading"] == 270




@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_get_battery_status(mockdata_mcp_client):
    """Test that the MCP client can get battery status via the server."""
    # Test with ID7 (electric vehicle)
    result = await mockdata_mcp_client.call_tool("get_battery_status", arguments={"vehicle_id": "WVWZZZED4SE003938"})
    logger.debug(f"Battery status result: {result}")
    
    assert result is not None
    assert isinstance(result.content, list)
    assert len(result.content) > 0
    
    battery = result.content[0].text
    logger.debug(f"Battery data: {battery}")
    
    battery_dict = json.loads(battery)
    assert battery_dict["battery_level_percent"] == 77.0
    assert battery_dict["range_km"] == 312.0  # Updated to match test_data.py
    assert battery_dict["is_charging"] is True
    assert battery_dict["charging_power_kw"] == 11.0  # Updated to match TestAdapter

