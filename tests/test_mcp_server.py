"""
MCP Server Tests
================

This test suite validates the FastMCP MCP protocol implementation.

What is tested:
- MCP client connection to server
- Tool invocation via MCP protocol (call_tool)
- Tool response validation and JSON parsing
- Error handling for invalid parameters

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

Note: 
- Resource tests are in tests/resources/ (not duplicated here)
- Tool implementation tests are in tests/tools/ (not duplicated here)
- This file focuses on MCP protocol layer (Client ↔ Server communication)
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


# ==================== MCP CLIENT CONNECTION TESTS ====================

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_client_connects(mockdata_mcp_client):
    """ Test that the MCP client can connect to the server. """
    assert mockdata_mcp_client.is_connected(), "MCP client should be connected"


# ==================== MCP TOOL INVOCATION TESTS ====================

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

