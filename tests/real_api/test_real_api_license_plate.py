"""Test to verify license plate availability from real VW API.

As of February 2026, VW WeConnect API does NOT provide license plates.
This test documents and verifies this limitation.

Usage:
    pytest tests/real_api/test_real_api_license_plate.py -v -s  # Run with real API
    pytest tests/ -m "not real_api"  # Skip in normal runs
"""

import pytest

pytestmark = [pytest.mark.real_api, pytest.mark.slow]


@pytest.mark.asyncio
async def test_license_plate_availability_from_real_api(real_adapter):
    """Verify VW API does NOT provide license plate information (known limitation)."""
    vehicles = real_adapter.list_vehicles()
    assert len(vehicles) > 0, "Test account should have at least one vehicle"
    
    vehicles_with_license_plate = 0
    
    print("\n" + "="*60)

    print("REAL VW API - LICENSE PLATE CHECK")
    print("="*60)
    
    for vehicle in vehicles:
        print(f"\nVehicle: {vehicle.name or 'Unknown'}")
        print(f"  Model: {vehicle.model or 'Unknown'}")
        print(f"  VIN: {vehicle.vin}")
        print(f"  License Plate: {vehicle.license_plate if vehicle.license_plate else '❌ NOT PROVIDED'}")
        
        if vehicle.license_plate:
            vehicles_with_license_plate += 1
    
    print(f"\n📊 Summary: {len(vehicles)} vehicle(s), {vehicles_with_license_plate} with license plate")
    print("="*60)
    
    assert vehicles_with_license_plate == 0, (
        f"Expected NO license plates (VW API limitation), but found {vehicles_with_license_plate}"
    )
    
    print("\n✅ CONFIRMED: VW API does NOT provide license plates (expected as of Feb 2026)")



@pytest.mark.asyncio
async def test_license_plate_field_exists_but_is_none(real_adapter):
    """Verify license_plate field exists but is None."""
    vehicles = real_adapter.list_vehicles()
    assert len(vehicles) > 0
    
    for vehicle in vehicles:
        assert hasattr(vehicle, 'license_plate')
        assert vehicle.license_plate is None
        print(f"✅ Vehicle {vehicle.vin}: license_plate = None (as expected)")


@pytest.mark.asyncio
async def test_adapter_layer_handles_missing_license_plate(real_adapter):
    """Verify adapter correctly handles missing license plate data."""
    vehicles = real_adapter.list_vehicles()
    assert len(vehicles) > 0
    
    print("\n" + "="*60)
    print("ADAPTER LAYER - LICENSE PLATE CHECK")
    print("="*60)
    
    for vehicle in vehicles:
        print(f"\nVehicle: {vehicle.name or vehicle.vin}")
        print(f"  VIN: {vehicle.vin}")
        print(f"  License Plate: {vehicle.license_plate if vehicle.license_plate else '❌ None'}")
        
        assert vehicle.license_plate is None, f"Should be None, got: {vehicle.license_plate}"
    
    print("\n✅ CONFIRMED: Adapter correctly returns None for license_plate")
    print("="*60)

