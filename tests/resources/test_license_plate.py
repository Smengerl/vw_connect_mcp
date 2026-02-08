"""Tests for license_plate field in VehicleModel.

Verifies that license_plate is correctly returned in get_vehicle() calls.
"""
import pytest
from src.weconnect_mcp.adapter.abstract_adapter import VehicleDetailLevel


def test_get_vehicle_returns_license_plate_basic(adapter):
    """Test that get_vehicle() returns license_plate with BASIC detail level."""
    vehicle = adapter.get_vehicle('WV2ZZZSTZNH009136', details=VehicleDetailLevel.BASIC)
    
    assert vehicle is not None
    assert vehicle.license_plate is not None
    assert vehicle.license_plate == 'M-AB 1234'


def test_get_vehicle_returns_license_plate_full(adapter):
    """Test that get_vehicle() returns license_plate with FULL detail level."""
    vehicle = adapter.get_vehicle('WV2ZZZSTZNH009136', details=VehicleDetailLevel.FULL)
    
    assert vehicle is not None
    assert vehicle.license_plate is not None
    assert vehicle.license_plate == 'M-AB 1234'


def test_get_vehicle_license_plate_for_all_vehicles(adapter):
    """Test that all vehicles have license_plate in get_vehicle()."""
    vehicles_list = adapter.list_vehicles()
    
    for vehicle_item in vehicles_list:
        vehicle = adapter.get_vehicle(vehicle_item.vin)
        assert vehicle is not None
        assert vehicle.license_plate == vehicle_item.license_plate, \
            f"License plate mismatch for VIN {vehicle_item.vin}"


def test_list_vehicles_returns_license_plate(adapter):
    """Test that list_vehicles() returns license_plate."""
    vehicles = adapter.list_vehicles()
    
    assert len(vehicles) == 2
    
    # Check first vehicle
    assert vehicles[0].license_plate is not None
    assert vehicles[0].license_plate == 'M-AB 1234'
    
    # Check second vehicle
    assert vehicles[1].license_plate is not None
    assert vehicles[1].license_plate == 'M-XY 5678'


def test_vehicle_model_has_license_plate_field(adapter):
    """Test that VehicleModel includes license_plate field."""
    vehicle = adapter.get_vehicle('WV2ZZZSTZNH009136')
    
    # Verify field exists in model
    assert hasattr(vehicle, 'license_plate')
    
    # Verify it's accessible
    license_plate = vehicle.license_plate
    assert license_plate is not None
