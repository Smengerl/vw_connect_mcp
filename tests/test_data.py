"""
Central Test Data Configuration
================================

This module provides centralized test data for all test suites, ensuring consistency
and avoiding duplication across test files.

Purpose:
- Single source of truth for test data
- Easy updates when mock data changes
- Prevents test failures due to inconsistent expected values
- Helper functions for parametrized tests

Contents:
1. Vehicle Identifiers (VINs, names, license plates)
2. Expected Values for Each Tool/Method
   - Vehicle info (electric & combustion)
   - Physical status (doors, windows, tyres, lights)
   - Energy status (battery, tank, range, charging)
   - Climate status (climatization, window heating)
   - Maintenance info (inspection, oil service)
   - Position (GPS coordinates, heading)
3. Helper Functions
   - get_electric_vehicle_identifiers()
   - get_combustion_vehicle_identifiers()
   - get_all_valid_identifiers()

Test Data Overview:
- Electric: ID.7 Tourer (VIN: WVWZZZED4SE003938, plate: M-XY 5678)
- Combustion: Transporter 7 (VIN: WV2ZZZSTZNH009136, plate: M-AB 1234)

All expected values match TestAdapter mock data exactly to ensure test accuracy.
"""

# ==================== VEHICLE IDs ====================

# Electric Vehicle (VW ID.7)
VIN_ELECTRIC = "WVWZZZED4SE003938"
NAME_ELECTRIC = "ID7"
LICENSE_PLATE_ELECTRIC = "M-XY 5678"

# Combustion Vehicle (VW T7)
VIN_COMBUSTION = "WV2ZZZSTZNH009136"
NAME_COMBUSTION = "T7"
LICENSE_PLATE_COMBUSTION = "M-AB 1234"  # Updated to match TestAdapter

# Invalid identifiers
VIN_INVALID = "INVALID_VIN"
VIN_NONEXISTENT = "NONEXISTENT"


# ==================== EXPECTED VALUES ====================

# Vehicle Info - Electric (ID.7)
EXPECTED_ELECTRIC_VEHICLE = {
    "vin": VIN_ELECTRIC,
    "name": NAME_ELECTRIC,
    "model": "ID.7 Tourer",  # Updated to match TestAdapter
    "manufacturer": "Volkswagen",
    "type": "electric",
    "license_plate": LICENSE_PLATE_ELECTRIC,
}

# Vehicle Info - Combustion (T7)
EXPECTED_COMBUSTION_VEHICLE = {
    "vin": VIN_COMBUSTION,
    "name": NAME_COMBUSTION,
    "model": "Transporter 7",  # Updated to match TestAdapter
    "manufacturer": "Volkswagen",
    "type": "combustion",
    "license_plate": LICENSE_PLATE_COMBUSTION,
}

# Physical Status
EXPECTED_PHYSICAL_STATUS_ID7 = {
    "doors_locked": True,
    "doors_closed": True,
    "windows_closed": True,
}

EXPECTED_PHYSICAL_STATUS_T7 = {
    "doors_locked": True,  # Updated: Both vehicles have locked doors in TestAdapter
    "doors_closed": True,
    "windows_closed": True,
}

# Energy Status - Electric
EXPECTED_ENERGY_ELECTRIC = {
    "vehicle_type": "electric",
    "battery_level_percent": 77.0,
    "total_range_km": 312.0,  # Updated to match TestAdapter
    "electric_range_km": 312.0,
    "is_charging": True,  # Updated: vehicle is charging in TestAdapter
}

# Energy Status - Combustion
EXPECTED_ENERGY_COMBUSTION = {
    "vehicle_type": "combustion",
    "total_range_km": 650.0,  # Updated to match TestAdapter
    "combustion_range_km": 650.0,
    "tank_level_percent": 68.0,  # Updated to match TestAdapter
}

# Climate Status - Electric (ID.7 - Active Heating)
EXPECTED_CLIMATE_ELECTRIC = {
    "climatization_state": "heating",
    "is_active": True,
    "target_temperature_celsius": 22.0,
    "window_heating_rear": "on",
}

# Climate Status - Combustion (T7 - Off)
EXPECTED_CLIMATE_COMBUSTION = {
    "climatization_state": "off",
    "is_active": False,
    "target_temperature_celsius": 21.0,
    "window_heating_rear": "off",
}

# Maintenance - Electric (no oil service)
EXPECTED_MAINTENANCE_ELECTRIC = {
    "inspection_due_date": "2026-08-15T00:00:00+00:00",
    "inspection_due_distance_km": 8500,
    "oil_service_due_date": None,
    "oil_service_due_distance_km": None,
}

# Maintenance - Combustion (with oil service)
EXPECTED_MAINTENANCE_COMBUSTION = {
    "inspection_due_date": "2026-05-20T00:00:00+00:00",
    "inspection_due_distance_km": 12000,
    "oil_service_due_date": "2026-04-10T00:00:00+00:00",
    "oil_service_due_distance_km": 8000,
}

# Position - ID.7 (Munich)
EXPECTED_POSITION_ELECTRIC = {
    "latitude": 48.1351,
    "longitude": 11.5820,
    "heading": 270,
}

# Position - T7 (Berlin)
EXPECTED_POSITION_COMBUSTION = {
    "latitude": 52.5200,
    "longitude": 13.4050,
    "heading": 90,
}


# ==================== HELPER FUNCTIONS ====================

def get_electric_vehicle_identifiers():
    """Return all valid identifiers for the electric test vehicle."""
    return [VIN_ELECTRIC, NAME_ELECTRIC, LICENSE_PLATE_ELECTRIC]


def get_combustion_vehicle_identifiers():
    """Return all valid identifiers for the combustion test vehicle."""
    return [VIN_COMBUSTION, NAME_COMBUSTION, LICENSE_PLATE_COMBUSTION]


def get_all_valid_identifiers():
    """Return all valid vehicle identifiers."""
    return get_electric_vehicle_identifiers() + get_combustion_vehicle_identifiers()


def get_invalid_identifiers():
    """Return invalid vehicle identifiers for negative testing."""
    return [VIN_INVALID, VIN_NONEXISTENT, "", "   "]
