import pytest
import json
from src.weconnect_mcp.server.mcp_server import get_server
from fastmcp import Client
from typing import Any
import logging
from src.weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter
import asyncio
import contextlib
from pathlib import Path
from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def config_path() -> Path:
    current_dir = Path(__file__).resolve().parent
    return (current_dir / "../src/config.json").resolve()


@pytest.fixture(scope="module")
def tokenstore_file() -> Path:
    current_dir = Path(__file__).resolve().parent
    return (current_dir / "../tmp/tokenstore").resolve()


@pytest.fixture(scope="module")
async def adapter(
    config_path: Path,
    tokenstore_file: Path,
) -> AsyncIterator[CarConnectivityAdapter]:
    logger.debug("1/7 Entering adapter fixture")
    async with CarConnectivityAdapter(
        config_path.as_posix(),
        tokenstore_file.as_posix(),
    ) as adapter:
        yield adapter
    logger.debug("7/7 Exiting adapter fixture")


@pytest.fixture(scope="module")
async def mcp_server(config_path: Path, adapter: CarConnectivityAdapter):
    logger.debug("2/7 Entering server fixture")
    server = get_server(adapter)
    finished = asyncio.Event()

    # wrap server run in a task that signals when finished for clean shutdown when task is cancelled
    async def run_and_signal():
        try:
            await server.run_stdio_async(show_banner=False)
        finally:
            finished.set()

    task = asyncio.create_task(run_and_signal())
    await asyncio.sleep(1)
    try:
        yield server
    finally:
        logger.debug("5/7 Exiting server fixture - start")
        task.cancel()
        await finished.wait()  
        logger.debug("6/7 Exiting server fixture")


@pytest.fixture(scope="function")
async def mcp_client(mcp_server):
    logger.debug("3/7 Entering mcp_client fixture")
    async with Client(mcp_server) as mcp_client:
        yield mcp_client
    logger.debug("4/7 Exiting mcp_client fixture")



def test_config_json_is_valid(config_path: Path):
    # Ensure the file exists
    assert config_path.exists(), f"Config file does not exist: {config_path}"
    assert config_path.is_file(), f"Path is not a file: {config_path}"

    # Try to parse the JSON content
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None
    except json.JSONDecodeError as e:
        raise AssertionError(f"Config contains invalid JSON: {e}") from e

    # Optional: ensure the JSON root is an object
    assert isinstance(data, dict), "Config JSON should be a dictionary at the top level"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_list_vehicles(mcp_client):
    """ Tests that the MCP client can list vehicles via the server. """
    result = await mcp_client.read_resource("data://list_vehicles")
    logger.debug(f"Resource read: {result}")
    assert result is not None, "Result from read_resource should not be None"
    assert result.__len__() == 1, f"Expected 1 result, got {result.__len__()}"
    assert hasattr(result[0], "text"), "Result[0] should have attribute 'text'"
    assert isinstance(result[0].text, str), "Result[0].text should be a string"

    all_vehicles_str = result[0].text
    vehicles = json.loads(all_vehicles_str)
    logger.debug(f"Found vehicles: {vehicles}")

    for vin in vehicles:
        assert isinstance(vin, str), f"VIN should be a string, got {type(vin)}"
        logger.debug(f"Reading details for vehicle: {vin}")

        result = await mcp_client.read_resource(f"data://state/{vin}")
        assert result is not None, f"Result for vehicle {vin} should not be None"
        assert result.__len__() == 1, f"Expected 1 result for vehicle {vin}, got {result.__len__()}"
        assert hasattr(result[0], "text"), f"Result[0] for vehicle {vin} should have attribute 'text'"
        assert isinstance(result[0].text, str), f"Result[0].text for vehicle {vin} should be a string"

        vehicle_str = result[0].text
        returned_vehicle = json.loads(vehicle_str)
        logger.debug(f"Vehicle details: {returned_vehicle}")