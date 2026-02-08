"""CarConnectivityAdapter Integration Tests with Real VW API.

⚠️ Requires valid VW credentials in src/config.json and internet connection.

Tests list_vehicles(), get_vehicle(), get_physical_status(), get_energy_status(),
get_climate_status(), get_maintenance_info(), and get_position() with real data.

Usage:
    pytest tests/real_api/test_real_api_carconnectivity_adapter.py -v  # Run with real API
    pytest tests/ -m "not real_api"  # Skip in normal runs
"""
import os
import pytest
from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter
from weconnect_mcp.adapter.abstract_adapter import VehicleModel, VehicleDetailLevel

import logging
logger = logging.getLogger(__name__)

# Mark all tests in this file as real_api and slow
pytestmark = [pytest.mark.real_api, pytest.mark.slow]


# ==================== TESTS ====================

def test_adapter_list_vehicles(real_adapter: CarConnectivityAdapter):
    """Test that list_vehicles returns valid vehicle data"""
    vehicles = real_adapter.list_vehicles()
    
    assert isinstance(vehicles, list)
    from weconnect_mcp.adapter.abstract_adapter import VehicleListItem
    assert all(isinstance(v, VehicleListItem) for v in vehicles)


def test_adapter_get_vehicle_basic_info(real_adapter: CarConnectivityAdapter):    
    """Test getting basic vehicle information for all vehicles"""
    vehicles = real_adapter.list_vehicles()
    
    for vehicle_info in vehicles:
        vin = vehicle_info.vin
        vehicle = real_adapter.get_vehicle(vin, details=VehicleDetailLevel.BASIC)
        
        assert isinstance(vehicle, VehicleModel)
        assert vehicle.vin == vin
        assert hasattr(vehicle, "model")
        assert hasattr(vehicle, "name")
        assert hasattr(vehicle, "manufacturer")
        assert hasattr(vehicle, "type")  # Changed from vehicle_type to type


def test_adapter_get_vehicle_full_info(real_adapter: CarConnectivityAdapter):
    """Test getting full vehicle information including state and software"""
    vehicles = real_adapter.list_vehicles()
    
    for vehicle_info in vehicles:
        vin = vehicle_info.vin
        vehicle = real_adapter.get_vehicle(vin, details=VehicleDetailLevel.FULL)
        
        assert isinstance(vehicle, VehicleModel)
        assert vehicle.vin == vin
        # Full detail fields
        assert hasattr(vehicle, "software_version")
        assert hasattr(vehicle, "model_year")
        assert hasattr(vehicle, "connection_state")
        assert hasattr(vehicle, "odometer")
        assert hasattr(vehicle, "state")


@pytest.mark.parametrize("vin", ["WVWZZZED4SE003938"])
async def test_get_physical_status_doors(real_adapter, vin):
    """Test getting door status via get_physical_status"""
    status = real_adapter.get_physical_status(vin, components=["doors"])
    
    assert status is not None
    assert status.doors is not None
    assert status.doors.rear_left is not None
    assert status.doors.rear_left.locked is not None
    assert status.doors.rear_left.open is not None
    assert status.doors.rear_right is not None
    assert status.doors.front_left is not None
    assert status.doors.front_right is not None
    assert status.doors.bonnet is not None
    assert status.doors.trunk is not None


@pytest.mark.parametrize("vin", ["WVWZZZED4SE003938"])
async def test_get_physical_status_windows(real_adapter, vin):
    """Test getting window status via get_physical_status"""
    status = real_adapter.get_physical_status(vin, components=["windows"])
    
    assert status is not None
    assert status.windows is not None
    assert status.windows.front_left is not None
    assert status.windows.front_left.open is not None
    assert status.windows.front_right is not None
    assert status.windows.rear_left is not None
    assert status.windows.rear_right is not None


@pytest.mark.parametrize("vin", ["WVWZZZED4SE003938"])
async def test_get_physical_status_tyres(real_adapter, vin):
    """Test getting tyre status via get_physical_status"""
    status = real_adapter.get_physical_status(vin, components=["tyres"])
    
    # Note: Tyre data may not always be available from VW API
    if status is not None and status.tyres is not None:
        assert status.tyres.front_left is not None
        assert status.tyres.front_right is not None
        assert status.tyres.rear_left is not None
        assert status.tyres.rear_right is not None


@pytest.mark.parametrize("vin", ["WVWZZZED4SE003938"])
async def test_get_physical_status_all_components(real_adapter, vin):
    """Test getting all physical components at once"""
    status = real_adapter.get_physical_status(vin)
    
    assert status is not None
    assert status.doors is not None
    assert status.windows is not None
    assert status.lights is not None
    # Tyres may be None if not available from API


@pytest.mark.parametrize("vin", ["WVWZZZED4SE003938"])
async def test_get_energy_status(real_adapter, vin):
    """Test getting energy status for electric vehicle"""
    energy = real_adapter.get_energy_status(vin)
    
    assert energy is not None
    assert energy.vehicle_type is not None
    assert energy.range is not None
    
    # For electric vehicles
    if energy.vehicle_type == "electric":
        assert energy.electric is not None
        assert hasattr(energy.electric, "battery_level_percent")  # Field exists
        assert energy.electric.charging is not None


@pytest.mark.parametrize("vin", ["WVWZZZED4SE003938"])
async def test_get_climate_status(real_adapter, vin):
    """Test getting climate status"""
    climate = real_adapter.get_climate_status(vin)
    
    assert climate is not None
    assert climate.climatization is not None
    assert hasattr(climate, "window_heating")  # Field exists, but may be None
