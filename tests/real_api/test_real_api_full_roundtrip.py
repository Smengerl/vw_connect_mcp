"""Full Roundtrip Integration Tests with Real VW API.

End-to-end tests validating complete MCP stack:
- Real VW API (via CarConnectivityAdapter)
- FastMCP server
- MCP client protocol
- Complete request/response cycle

⚠️ Requires valid VW credentials in src/config.json and internet connection.

Usage:
    pytest tests/real_api/test_real_api_full_roundtrip.py -v  # Run with real API
    pytest tests/ -m "not real_api"  # Skip in normal runs
"""
import pytest
import json

import logging
logger = logging.getLogger(__name__)

# Mark all tests in this file as real_api and slow
pytestmark = [pytest.mark.real_api, pytest.mark.slow]


# ==================== TESTS ====================

def test_config_json_is_valid(config_path):
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
async def test_mcp_list_vehicles(real_mcp_client):
    """ Tests that the MCP client can list vehicles via the server. """
    result = await real_mcp_client.read_resource("data://vehicles")
    logger.debug(f"Resource read: {result}")
    assert result is not None, "Result from read_resource should not be None"
    assert result.__len__() == 1, f"Expected 1 result, got {result.__len__()}"
    assert hasattr(result[0], "text"), "Result[0] should have attribute 'text'"
    assert isinstance(result[0].text, str), "Result[0].text should be a string"

    all_vehicles_str = result[0].text
    vehicles = json.loads(all_vehicles_str)
    logger.debug(f"Found vehicles: {vehicles}")

    # vehicles are now dicts with vin, name, model
    for vehicle_info in vehicles:
        assert isinstance(vehicle_info, dict), f"vehicle_info should be a dict, got {type(vehicle_info)}"
        assert "vin" in vehicle_info, "vehicle_info should have a 'vin' key"
        vin = vehicle_info["vin"]
        logger.debug(f"Reading details for vehicle: {vin}")

        result = await real_mcp_client.read_resource(f"data://vehicle/{vin}/state")
        assert result is not None, f"Result for vehicle {vin} should not be None"
        assert result.__len__() == 1, f"Expected 1 result for vehicle {vin}, got {result.__len__()}"
        assert hasattr(result[0], "text"), f"Result[0] for vehicle {vin} should have attribute 'text'"
        assert isinstance(result[0].text, str), f"Result[0].text for vehicle {vin} should be a string"

        vehicle_str = result[0].text
        returned_vehicle = json.loads(vehicle_str)
        logger.debug(f"Vehicle details: {returned_vehicle}")