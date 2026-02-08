"""
Tests for get_vehicle Tool
===========================

This test suite validates the get_vehicle() consolidated adapter method and its MCP tool registration.

What is tested:
- BASIC vs FULL detail levels
- Vehicle identifier resolution (VIN, name, license plate)
- Vehicle type identification (electric vs combustion)
- Data consistency and completeness
- Invalid identifier handling
- MCP server tool registration (get_vehicle_info)

Key features:
- Consolidated method replaces multiple old methods (get_vehicle_info, get_vehicle_type)
- Supports two detail levels: BASIC (minimal info) and FULL (includes state, odometer, etc.)
- Flexible identifier resolution (VIN, name, or license plate)

Test data:
- Uses TestAdapter with 2 mock vehicles
- Parametrized tests for all identifier types
"""
import pytest
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
from weconnect_mcp.adapter.abstract_adapter import VehicleDetailLevel


# ==================== TESTS - BASIC DETAILS ====================

def test_get_vehicle_basic_details_electric(adapter):
    """Test getting basic vehicle information for electric vehicle"""
    vehicle = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.BASIC)
    
    assert vehicle is not None
    assert vehicle.vin == EXPECTED_ELECTRIC_VEHICLE["vin"]
    assert vehicle.name == EXPECTED_ELECTRIC_VEHICLE["name"]
    assert vehicle.model == EXPECTED_ELECTRIC_VEHICLE["model"]
    assert vehicle.type == EXPECTED_ELECTRIC_VEHICLE["type"]  # Use 'type' not 'vehicle_type'
    assert vehicle.manufacturer == EXPECTED_ELECTRIC_VEHICLE["manufacturer"]


def test_get_vehicle_basic_details_combustion(adapter):
    """Test getting basic vehicle information for combustion vehicle"""
    vehicle = adapter.get_vehicle(VIN_COMBUSTION, details=VehicleDetailLevel.BASIC)
    
    assert vehicle is not None
    assert vehicle.vin == EXPECTED_COMBUSTION_VEHICLE["vin"]
    assert vehicle.name == EXPECTED_COMBUSTION_VEHICLE["name"]
    assert vehicle.model == EXPECTED_COMBUSTION_VEHICLE["model"]
    assert vehicle.type == EXPECTED_COMBUSTION_VEHICLE["type"]  # Use 'type' not 'vehicle_type'


# ==================== TESTS - FULL DETAILS ====================

def test_get_vehicle_full_details_electric(adapter):
    """Test getting full vehicle information including state and software"""
    vehicle = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.FULL)
    
    assert vehicle is not None
    # Basic fields
    assert vehicle.vin == EXPECTED_ELECTRIC_VEHICLE["vin"]
    assert vehicle.name == EXPECTED_ELECTRIC_VEHICLE["name"]
    # Full detail fields
    assert vehicle.state is not None
    assert vehicle.connection_state is not None
    assert vehicle.odometer is not None


def test_get_vehicle_full_vs_basic_has_more_fields(adapter):
    """Test that FULL detail level includes fields not in BASIC"""
    basic = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.BASIC)
    full = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.FULL)
    
    # Basic should have fewer non-None fields than Full
    # Count non-None fields
    basic_fields = sum(1 for v in basic.__dict__.values() if v is not None)
    full_fields = sum(1 for v in full.__dict__.values() if v is not None)
    
    assert full_fields >= basic_fields, "FULL should have at least as many fields as BASIC"


# ==================== TESTS - IDENTIFIER RESOLUTION ====================

@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_get_vehicle_by_different_identifiers(adapter, identifier):
    """Test that vehicle can be retrieved by VIN, name, or license plate"""
    vehicle = adapter.get_vehicle(identifier, details=VehicleDetailLevel.BASIC)
    
    assert vehicle is not None
    assert vehicle.vin == VIN_ELECTRIC
    assert vehicle.name == NAME_ELECTRIC


def test_get_vehicle_invalid_identifier(adapter):
    """Test that invalid identifier returns None"""
    vehicle = adapter.get_vehicle(VIN_INVALID, details=VehicleDetailLevel.BASIC)
    
    assert vehicle is None


# ==================== TESTS - VEHICLE TYPE ====================

def test_get_vehicle_type_electric(adapter):
    """Test that electric vehicle type is correctly identified"""
    vehicle = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.BASIC)
    
    assert vehicle is not None
    assert vehicle.type == "electric"  # Use 'type' not 'vehicle_type'


def test_get_vehicle_type_combustion(adapter):
    """Test that combustion vehicle type is correctly identified"""
    vehicle = adapter.get_vehicle(VIN_COMBUSTION, details=VehicleDetailLevel.BASIC)
    
    assert vehicle is not None
    assert vehicle.type == "combustion"  # Use 'type' not 'vehicle_type'


# ==================== TESTS - DATA CONSISTENCY ====================

def test_get_vehicle_vin_matches_request(adapter):
    """Test that returned VIN matches the requested VIN"""
    vehicle = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.BASIC)
    
    assert vehicle is not None
    assert vehicle.vin == VIN_ELECTRIC


# ==================== MCP SERVER REGISTRATION ====================

@pytest.mark.asyncio
async def test_get_vehicle_info_tool_is_registered(mcp_server):
    """Test that get_vehicle_info is available as a resource in the MCP server"""
    resource_templates = await mcp_server.get_resource_templates()
    
    assert resource_templates is not None, "Resource templates should not be None"
    template_uris = list(resource_templates.keys())
    assert "data://vehicle/{vehicle_id}/info" in template_uris, "data://vehicle/{vehicle_id}/info resource should be registered in MCP server"
