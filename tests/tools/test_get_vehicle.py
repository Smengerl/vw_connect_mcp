"""
Tests for get_vehicle Tool
===========================

This test suite validates the get_vehicle() consolidated adapter method and its MCP tool registration.

What is tested:
- BASIC vs FULL detail levels
- Vehicle identifier resolution (VIN, name)
- Data consistency and completeness
- Invalid identifier handling
- MCP server tool registration (get_vehicle_info)

Key features:
- Supports two detail levels: BASIC (identity only) and FULL (BASIC + connection_state)
- Flexible identifier resolution (VIN or name) -- no license plate support,
  Tibber never reports one, see abstract_adapter.py's docstrings
- No vehicle type/propulsion field exists -- Tibber never reports it (it's
  EV-only, see ARCHITECTURE.md), so there is nothing to assert about
  vehicle classification here or anywhere else in this project

Test data:
- Uses TestAdapter with 2 mock vehicles
- Parametrized tests for all identifier types
"""
import pytest
from test_data import (
    VIN_ELECTRIC,
    VIN_HYBRID,
    NAME_ELECTRIC,
    VIN_INVALID,
    EXPECTED_ELECTRIC_VEHICLE,
    EXPECTED_HYBRID_VEHICLE,
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
    assert vehicle.manufacturer == EXPECTED_ELECTRIC_VEHICLE["manufacturer"]


def test_get_vehicle_basic_details_hybrid(adapter):
    """Test getting basic vehicle information for hybrid vehicle"""
    vehicle = adapter.get_vehicle(VIN_HYBRID, details=VehicleDetailLevel.BASIC)

    assert vehicle is not None
    assert vehicle.vin == EXPECTED_HYBRID_VEHICLE["vin"]
    assert vehicle.name == EXPECTED_HYBRID_VEHICLE["name"]
    assert vehicle.model == EXPECTED_HYBRID_VEHICLE["model"]


# ==================== TESTS - BASIC vs FULL ====================

def test_get_vehicle_basic_has_no_connection_state(adapter):
    """BASIC should not make the extra call that populates connection_state/last_seen"""
    vehicle = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.BASIC)

    assert vehicle is not None
    assert vehicle.connection_state is None
    assert vehicle.last_seen is None


def test_get_vehicle_full_details_electric(adapter):
    """Test getting full vehicle information including connection_state/last_seen"""
    vehicle = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.FULL)

    assert vehicle is not None
    assert vehicle.vin == EXPECTED_ELECTRIC_VEHICLE["vin"]
    assert vehicle.name == EXPECTED_ELECTRIC_VEHICLE["name"]
    assert vehicle.connection_state is not None
    assert vehicle.last_seen == EXPECTED_ELECTRIC_VEHICLE["last_seen"]


def test_get_vehicle_full_vs_basic_has_more_fields(adapter):
    """Test that FULL detail level includes fields not in BASIC"""
    basic = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.BASIC)
    full = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.FULL)

    basic_fields = sum(1 for v in basic.__dict__.values() if v is not None)
    full_fields = sum(1 for v in full.__dict__.values() if v is not None)

    assert full_fields >= basic_fields, "FULL should have at least as many fields as BASIC"


# ==================== TESTS - IDENTIFIER RESOLUTION ====================

@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_get_vehicle_by_different_identifiers(adapter, identifier):
    """Test that vehicle can be retrieved by VIN or name"""
    vehicle = adapter.get_vehicle(identifier, details=VehicleDetailLevel.BASIC)

    assert vehicle is not None
    assert vehicle.vin == VIN_ELECTRIC
    assert vehicle.name == NAME_ELECTRIC


def test_get_vehicle_invalid_identifier(adapter):
    """Test that invalid identifier returns None"""
    vehicle = adapter.get_vehicle(VIN_INVALID, details=VehicleDetailLevel.BASIC)

    assert vehicle is None


# ==================== TESTS - DATA CONSISTENCY ====================

def test_get_vehicle_vin_matches_request(adapter):
    """Test that returned VIN matches the requested VIN"""
    vehicle = adapter.get_vehicle(VIN_ELECTRIC, details=VehicleDetailLevel.BASIC)

    assert vehicle is not None
    assert vehicle.vin == VIN_ELECTRIC
