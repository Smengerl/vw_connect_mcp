import pytest
import json
from src.weconnect_mcp.server.mcp_server import get_server
from .test_adapter import TestAdapter, MockVehicle
from fastmcp import Client
from typing import Any
import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def adapter():
    return TestAdapter()

@pytest.fixture(scope="module")
def mcp_server(adapter):
    return get_server(adapter)

@pytest.fixture(scope="function")
async def mcp_client(mcp_server):
    async with Client(mcp_server) as mcp_client:
        yield mcp_client


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_resources_registered(mcp_server: Any):
    """ Make sure that the MCP server has registered the expected resources. """
    all_resources = await mcp_server.get_resources()
    logger.info(f"Registered resources: {list(all_resources.keys())}")
    assert all_resources is not None
    assert "data://list_vehicles" in all_resources
    all_resource_templates = await mcp_server.get_resource_templates()
    assert all_resource_templates is not None
    assert "data://state/{vehicle_id}" in all_resource_templates


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_resources_provide_valid_data(mcp_server: Any):
    """ Test that the MCP server resources return valid data. """
    # List vehicles
    vehicles_resource = await mcp_server.get_resource("data://list_vehicles")
    assert vehicles_resource is not None

    all_vehicles_str = await vehicles_resource.read()
    assert all_vehicles_str is not None
    logger.info(f"All vehicles string: {all_vehicles_str}")

    vehicles = json.loads(all_vehicles_str)
    assert isinstance(vehicles, list)
    assert len(vehicles) == TestAdapter.vehicles.__len__()

    # Get state for each vehicle
    for vehicle_id in vehicles:
        logger.info(f"Try resource: data://state/{vehicle_id}")
        state_resource_template = await mcp_server.get_resource_template("data://state/{vehicle_id}")
        assert state_resource_template is not None

        vehicle_str = await state_resource_template.read({"vehicle_id": vehicle_id})
        assert vehicle_str is not None
        logger.info(f"Vehicle string: {vehicle_str}")
        assert isinstance(vehicle_str, MockVehicle)


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_client_connects(mcp_client):
    """ Test that the MCP client can connect to the server. """
    assert mcp_client.is_connected()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_list_vehicles(mcp_client):
    """ Tests that the MCP client can list vehicles via the server. """
    logger.info(f"Testing MCP list vehicles...")
    result = await mcp_client.read_resource("data://list_vehicles")
    logger.info(f"Resource read: {result}")
    assert result is not None
    assert result.__len__() == 1
    assert hasattr(result[0], "text")
    assert isinstance(result[0].text, str)


    all_vehicles_str = result[0].text
    logger.info(f"All vehicles string from client: {all_vehicles_str}")
    vehicles = json.loads(all_vehicles_str)
    logger.info(f"Deserialized JSON from client: {vehicles}")

    assert vehicles.__len__() == TestAdapter.vehicles.__len__()
    for vin in vehicles:
        assert isinstance(vin, str)
        if vin in [v.vin for v in TestAdapter.vehicles]:
            logger.info(f"Found vehicle VIN from client: {vin}")
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
async def test_mcp_get_vehicle_state(mcp_client, vehicle):
    """ Tests that the MCP client can get the state of a vehicle via the server. """
    result = await mcp_client.read_resource(f"data://state/{vehicle.vin}")
    logger.info(f"Vehicle state string for vehicle {vehicle.vin} from client: {result[0].text}")
    assert result is not None
    assert result.__len__() == 1
    assert hasattr(result[0], "text")
    assert isinstance(result[0].text, str)

    vehicle_str = result[0].text
    logger.info(f"Vehicle string from client: {vehicle_str}")
    returned_vehicle = json.loads(vehicle_str)
    logger.info(f"Deserialized JSON from client: {returned_vehicle}")
    assert returned_vehicle["vin"] == vehicle.vin
    assert returned_vehicle["model"] == vehicle.model
    assert returned_vehicle["manufacturer"] == vehicle.manufacturer
    assert returned_vehicle["state"] == vehicle.state
    assert returned_vehicle["type"] == vehicle.type
    assert returned_vehicle["odometer"] == vehicle.odometer
    assert returned_vehicle["position"] == vehicle.position
    assert returned_vehicle["capabilities"] == vehicle.capabilities