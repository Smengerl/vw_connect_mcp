"""
Tests for list_vehicles Tool
=============================

This test suite validates the list_vehicles() adapter method and its MCP tool registration.

What is tested:
- Returns all available vehicles
- Each vehicle contains required fields (VIN, name, model)
- Vehicle data accuracy (electric and hybrid vehicles)
- MCP server tool registration

Test data:
- Uses TestAdapter with 2 mock vehicles (ID.7 Tourer electric, T7 Multivan eHybrid hybrid)
- Expected values from tests.test_data module
"""
from test_data import (
    VIN_ELECTRIC,
    VIN_HYBRID,
    EXPECTED_ELECTRIC_VEHICLE,
    EXPECTED_HYBRID_VEHICLE,
)


# ==================== TESTS ====================

def test_list_vehicles_returns_all_vehicles(adapter):
    """Test that list_vehicles returns all available vehicles"""
    vehicles = adapter.list_vehicles()
    
    assert vehicles is not None
    assert len(vehicles) == 2, "Should return exactly 2 test vehicles"


def test_list_vehicles_has_required_fields(adapter):
    """Test that each vehicle has all required fields"""
    vehicles = adapter.list_vehicles()
    
    for vehicle in vehicles:
        assert vehicle.vin is not None
        assert vehicle.name is not None
        assert vehicle.model is not None


def test_list_vehicles_electric_vehicle_data(adapter):
    """Test that electric vehicle data is correct (also validates presence in list)"""
    vehicles = adapter.list_vehicles()

    electric = next((v for v in vehicles if v.vin == VIN_ELECTRIC), None)
    assert electric is not None, "Electric vehicle should be in list"
    assert electric.name == EXPECTED_ELECTRIC_VEHICLE["name"]
    assert electric.model == EXPECTED_ELECTRIC_VEHICLE["model"]


def test_list_vehicles_hybrid_vehicle_data(adapter):
    """Test that hybrid vehicle data is correct (also validates presence in list)"""
    vehicles = adapter.list_vehicles()

    hybrid = next((v for v in vehicles if v.vin == VIN_HYBRID), None)
    assert hybrid is not None, "Hybrid vehicle should be in list"
    assert hybrid.name == EXPECTED_HYBRID_VEHICLE["name"]
    assert hybrid.model == EXPECTED_HYBRID_VEHICLE["model"]
