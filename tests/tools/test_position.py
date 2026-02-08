"""
Tests for get_position Tool
============================

This test suite validates the get_position() adapter method and MCP tool registration.

What is tested:
- Electric vehicle GPS position (Munich coordinates)
- Combustion vehicle GPS position (Berlin coordinates)
- Coordinate validity ranges (latitude: -90 to 90, longitude: -180 to 180)
- Heading validity range (0 to 360 degrees)
- Invalid vehicle handling
- MCP server tool registration

Key features:
- Standalone method (not replaced by consolidation)
- GPS coordinates (latitude, longitude)
- Compass heading (0=North, 90=East, 180=South, 270=West)
- Applicable to all vehicle types

Test data:
- Electric vehicle: Munich, Germany (48.1351°N, 11.5820°E, heading 45°)
- Combustion vehicle: Berlin, Germany (52.5200°N, 13.4050°E, heading 180°)
"""
import pytest
from test_data import (
    VIN_ELECTRIC,
    VIN_COMBUSTION,
    VIN_NONEXISTENT,
    EXPECTED_POSITION_ELECTRIC,
    EXPECTED_POSITION_COMBUSTION,
)


# ==================== TESTS ====================

def test_get_position_electric_vehicle(adapter):
    """Test getting position for electric vehicle (Munich)"""
    position = adapter.get_position(VIN_ELECTRIC)
    
    assert position is not None
    assert position.latitude == EXPECTED_POSITION_ELECTRIC["latitude"]
    assert position.longitude == EXPECTED_POSITION_ELECTRIC["longitude"]
    assert position.heading == EXPECTED_POSITION_ELECTRIC["heading"]


def test_get_position_combustion_vehicle(adapter):
    """Test getting position for combustion vehicle (Berlin)"""
    position = adapter.get_position(VIN_COMBUSTION)
    
    assert position is not None
    assert position.latitude == EXPECTED_POSITION_COMBUSTION["latitude"]
    assert position.longitude == EXPECTED_POSITION_COMBUSTION["longitude"]
    assert position.heading == EXPECTED_POSITION_COMBUSTION["heading"]


def test_get_position_nonexistent_vehicle(adapter):
    """Test getting position for non-existent vehicle"""
    position = adapter.get_position(VIN_NONEXISTENT)
    
    assert position is None


def test_position_coordinates_valid_ranges(adapter):
    """Test that position coordinates are in valid ranges"""
    position = adapter.get_position(VIN_ELECTRIC)
    
    assert position is not None
    assert -90 <= position.latitude <= 90, "Latitude must be between -90 and 90"
    assert -180 <= position.longitude <= 180, "Longitude must be between -180 and 180"
    assert 0 <= position.heading <= 360, "Heading must be between 0 and 360"


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_get_position_tool_is_registered(mcp_server):
    """Test that get_position is available as a resource in the MCP server"""
    resource_templates = await mcp_server.get_resource_templates()
    
    assert resource_templates is not None, "Resource templates should not be None"
    template_uris = list(resource_templates.keys())
    assert "data://vehicle/{vehicle_id}/position" in template_uris, "data://vehicle/{vehicle_id}/position resource should be registered in MCP server"
