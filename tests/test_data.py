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
1. Vehicle Identifiers (VINs, names)
2. Expected Values for Each Tool/Method
   - Vehicle info (electric & hybrid)
   - Energy status (battery, tank, range, charging)
3. Helper Functions
   - get_electric_vehicle_identifiers()
   - get_hybrid_vehicle_identifiers()
   - get_all_valid_identifiers()

Test Data Overview (both vehicles are electric -- Tibber's Enode-backed
integration is EV-only, see ARCHITECTURE.md; the second vehicle exists to
exercise multi-vehicle identifier resolution, not a different energy-data
shape). No license plates either -- Tibber's Data API never reports one,
so there's no field for it and no identifier-resolution path for it
either (see abstract_adapter.py's docstrings):
- ID.7 Tourer (VIN: WVWZZZED4SE003938)
- T7 Multivan eHybrid (VIN: WV2ZZZSTZNH009136) -- keeps its real-world
  "eHybrid" name, but its energy data is the same electric shape as any
  other Tibber-reported vehicle (see TestAdapter's docstring)

All expected values match TestAdapter mock data exactly to ensure test accuracy.
"""

# ==================== VEHICLE IDs ====================

# ID.7 Tourer
VIN_ELECTRIC = "WVWZZZED4SE003938"
NAME_ELECTRIC = "ID7"

# T7 Multivan eHybrid -- second vehicle for identifier-resolution coverage,
# not a different energy-data shape (see module docstring)
VIN_HYBRID = "WV2ZZZSTZNH009136"
NAME_HYBRID = "T7"

# Invalid identifiers
VIN_INVALID = "INVALID_VIN"
VIN_NONEXISTENT = "NONEXISTENT"


# ==================== EXPECTED VALUES ====================

# Vehicle Info - ID.7
EXPECTED_ELECTRIC_VEHICLE = {
    "vin": VIN_ELECTRIC,
    "name": NAME_ELECTRIC,
    "model": "ID.7 Tourer",
    "manufacturer": "Volkswagen",
    "last_seen": "2024-01-15T10:31:00Z",
}

# Vehicle Info - T7 Multivan eHybrid
EXPECTED_HYBRID_VEHICLE = {
    "vin": VIN_HYBRID,
    "name": NAME_HYBRID,
    "model": "Multivan eHybrid",
    "manufacturer": "Volkswagen",
    "last_seen": "2024-01-15T10:30:00Z",
}

# Energy Status - ID.7
EXPECTED_ENERGY_ELECTRIC = {
    "battery_level_percent": 77.0,
    "range_km": 312.0,
    "is_charging": True,
    "last_seen": "2024-01-15T10:31:00Z",
}

# Energy Status - T7 Multivan eHybrid (same shape as any other vehicle
# Tibber reports -- see module docstring)
EXPECTED_ENERGY_HYBRID = {
    "battery_level_percent": 64.0,
    "range_km": 630.0,
    "is_charging": False,
    "is_plugged_in": True,
    "last_seen": "2024-01-15T10:30:00Z",
}


# ==================== HELPER FUNCTIONS ====================

def get_electric_vehicle_identifiers():
    """Return all valid identifiers for the ID.7 test vehicle."""
    return [VIN_ELECTRIC, NAME_ELECTRIC]


def get_hybrid_vehicle_identifiers():
    """Return all valid identifiers for the T7 Multivan eHybrid test vehicle."""
    return [VIN_HYBRID, NAME_HYBRID]


def get_all_valid_identifiers():
    """Return all valid vehicle identifiers."""
    return get_electric_vehicle_identifiers() + get_hybrid_vehicle_identifiers()


def get_invalid_identifiers():
    """Return invalid vehicle identifiers for negative testing."""
    return [VIN_INVALID, VIN_NONEXISTENT, "", "   "]
