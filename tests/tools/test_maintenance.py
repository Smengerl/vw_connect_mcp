"""
Tests for get_maintenance_info Tool
====================================

This test suite validates the get_maintenance_info() adapter method and MCP tool registration.

What is tested:
- Electric vehicle maintenance info (inspection only, no oil service)
- Combustion vehicle maintenance info (inspection and oil service)
- Inspection due dates and distances
- Oil service due dates and distances (combustion only)
- Invalid vehicle handling
- MCP server tool registration

Key features:
- Standalone method (not replaced by consolidation)
- Vehicle type-specific data (oil service only for combustion/hybrid)
- Inspection maintenance applicable to all vehicle types
- ISO date format for due dates

Test data:
- Electric vehicle: Inspection due in 15,000 km
- Combustion vehicle: Inspection due in 12,000 km, oil service in 18,000 km
"""
import pytest
from test_data import (
    VIN_ELECTRIC,
    VIN_COMBUSTION,
    VIN_INVALID,
    EXPECTED_MAINTENANCE_ELECTRIC,
    EXPECTED_MAINTENANCE_COMBUSTION,
)


# ==================== TESTS ====================

def test_get_maintenance_info_electric(adapter):
    """Test getting maintenance info for electric vehicle (no oil service)"""
    maintenance = adapter.get_maintenance_info(VIN_ELECTRIC)
    
    assert maintenance is not None
    assert maintenance.inspection_due_date == EXPECTED_MAINTENANCE_ELECTRIC["inspection_due_date"]
    assert maintenance.inspection_due_distance_km == EXPECTED_MAINTENANCE_ELECTRIC["inspection_due_distance_km"]
    assert maintenance.oil_service_due_date is None
    assert maintenance.oil_service_due_distance_km is None


def test_get_maintenance_info_combustion(adapter):
    """Test getting maintenance info for combustion vehicle (has oil service)"""
    maintenance = adapter.get_maintenance_info(VIN_COMBUSTION)
    
    assert maintenance is not None
    assert maintenance.inspection_due_date == EXPECTED_MAINTENANCE_COMBUSTION["inspection_due_date"]
    assert maintenance.inspection_due_distance_km == EXPECTED_MAINTENANCE_COMBUSTION["inspection_due_distance_km"]
    assert maintenance.oil_service_due_date == EXPECTED_MAINTENANCE_COMBUSTION["oil_service_due_date"]
    assert maintenance.oil_service_due_distance_km == EXPECTED_MAINTENANCE_COMBUSTION["oil_service_due_distance_km"]


def test_get_maintenance_info_invalid_vehicle(adapter):
    """Test getting maintenance info for non-existent vehicle"""
    maintenance = adapter.get_maintenance_info(VIN_INVALID)
    
    assert maintenance is None


def test_maintenance_info_has_inspection_due(adapter):
    """Test that maintenance info correctly shows upcoming inspection"""
    maintenance = adapter.get_maintenance_info(VIN_ELECTRIC)
    
    assert maintenance is not None
    assert maintenance.inspection_due_distance_km is not None
    assert maintenance.inspection_due_distance_km > 0


def test_maintenance_info_oil_service_only_combustion(adapter):
    """Test that oil service is only present for combustion vehicles"""
    # Electric vehicle should have no oil service
    electric_maintenance = adapter.get_maintenance_info(VIN_ELECTRIC)
    assert electric_maintenance is not None
    assert electric_maintenance.oil_service_due_date is None
    
    # Combustion vehicle should have oil service
    combustion_maintenance = adapter.get_maintenance_info(VIN_COMBUSTION)
    assert combustion_maintenance is not None
    assert combustion_maintenance.oil_service_due_date is not None


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_get_maintenance_info_tool_is_registered(mcp_server):
    """Test that get_maintenance_info tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    
    assert tools is not None, "Tools should not be None"
    tool_names = list(tools.keys())
    assert "get_maintenance_info" in tool_names, "get_maintenance_info tool should be registered in MCP server"
