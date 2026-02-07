import pytest
import json
from src.weconnect_mcp.server.mcp_server import get_server
from .test_adapter import TestAdapter
from weconnect_mcp.adapter.carconnectivity_adapter import VehicleModel
from fastmcp import Client
from typing import Any

import logging
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def mockdata_adapter():
    return TestAdapter()

@pytest.fixture(scope="module")
def mockdata_mcp_server(mockdata_adapter):
    return get_server(mockdata_adapter)

@pytest.fixture(scope="function")
async def mockdata_mcp_client(mockdata_mcp_server):
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

    # Get state for each vehicle
    for vehicle_id in vehicles:
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
    for vin in vehicles:
        assert isinstance(vin, str), f"VIN should be a string, got {type(vin)}"
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
