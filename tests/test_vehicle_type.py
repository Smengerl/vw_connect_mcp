"""Tests for the vehicle type functionality."""

import pytest
from tests.test_adapter import TestAdapter
from .test_adapter import TestAdapter

@pytest.mark.parametrize(
    "vehicle",
    [
        (TestAdapter.vehicles[0]),
        (TestAdapter.vehicles[1]),
    ],
)
def test_get_vehicle_type_valid(vehicle):
    """Test that get_vehicle_type returns correct type for valid VIN."""
    adapter = TestAdapter()
    
    vehicle_type = adapter.get_vehicle_type(vehicle.vin)
    assert vehicle_type == vehicle.type, f"Expected '{vehicle.type}', got {vehicle_type}"



def test_get_vehicle_type_invalid():
    """Test that get_vehicle_type returns None for invalid VIN."""
    adapter = TestAdapter()
    
    vehicle_type = adapter.get_vehicle_type("INVALID_VIN")
    assert vehicle_type is None, f"Expected None, got {vehicle_type}"


def test_get_vehicle_type_mcp_tool():
    """Test the get_vehicle_type MCP tool."""
    from weconnect_mcp.server.mcp_server import get_server
    
    adapter = TestAdapter()
    mcp = get_server(adapter)
    
    # Check that the tool is registered
    assert hasattr(mcp, 'get_tool'), "MCP server should have get_tool method"
    
    print("MCP server created successfully with vehicle type tool")
