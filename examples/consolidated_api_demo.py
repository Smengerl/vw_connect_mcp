#!/usr/bin/env python3
"""
Demo: Consolidated API (New Architecture)

This script demonstrates the new consolidated API structure introduced
to reduce MCP tool count and improve maintainability.

Key improvements over old API:
- Fewer tools: 3 status methods instead of 10+ individual methods
- Better organization: Physical, Energy, Climate categories
- Flexible detail levels: BASIC vs FULL
- Component filtering: Request only what you need
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_adapter import TestAdapter
from weconnect_mcp.adapter.abstract_adapter import VehicleDetailLevel


def print_section(title: str, char: str = "="):
    """Print a formatted section header"""
    print(f"\n{char*70}")
    print(f"  {title}")
    print(f"{char*70}\n")


def demo_vehicle_info():
    """Demonstrate get_vehicle() with detail levels"""
    print_section("🚗 VEHICLE INFO - Detail Levels", "=")
    
    adapter = TestAdapter()
    vin = 'WVWZZZED4SE003938'  # ID7 Electric
    
    # BASIC: Essential identifiers only
    print("1. BASIC Detail Level (Essential Info)")
    print("-" * 70)
    vehicle = adapter.get_vehicle(vin, details=VehicleDetailLevel.BASIC)
    print(f"   VIN: {vehicle.vin}")
    print(f"   Name: {vehicle.name}")
    print(f"   Model: {vehicle.model}")
    print(f"   License Plate: {vehicle.license_plate}")
    print(f"   Type: {vehicle.type}")
    print(f"   Manufacturer: {vehicle.manufacturer}")
    
    # FULL: Includes state, odometer, software, etc.
    print("\n2. FULL Detail Level (Adds State & Diagnostics)")
    print("-" * 70)
    vehicle = adapter.get_vehicle(vin, details=VehicleDetailLevel.FULL)
    print(f"   State: {vehicle.state}")
    print(f"   Connection: {vehicle.connection_state}")
    print(f"   Odometer: {vehicle.odometer} km")
    print(f"   Software: {vehicle.software_version}")
    print(f"   Model Year: {vehicle.model_year}")


def demo_physical_status():
    """Demonstrate get_physical_status() with component filtering"""
    print_section("🔧 PHYSICAL STATUS - Component Filtering", "=")
    
    adapter = TestAdapter()
    vin = 'WVWZZZED4SE003938'
    
    # Request ALL components (default)
    print("1. All Components (Default)")
    print("-" * 70)
    status = adapter.get_physical_status(vin)
    print(f"   Doors Locked: {status.doors.lock_state if status.doors else 'N/A'}")
    if status.windows and status.windows.front_left:
        print(f"   Front Left Window: {'Open' if status.windows.front_left.open else 'Closed'}")
    else:
        print(f"   Windows: N/A")
    print(f"   Tyres Pressure OK: {status.tyres.pressure_ok if status.tyres else 'N/A'}")
    if status.lights and status.lights.left:
        print(f"   Left Light: {status.lights.left.state}")
    else:
        print(f"   Lights: N/A")
    
    # Request ONLY doors
    print("\n2. Only Doors (Filtered)")
    print("-" * 70)
    status = adapter.get_physical_status(vin, components=['doors'])
    print(f"   Doors Locked: {status.doors.lock_state if status.doors else 'N/A'}")
    print(f"   Windows: {status.windows}")  # None
    print(f"   Tyres: {status.tyres}")  # None
    print(f"   Lights: {status.lights}")  # None
    
    # Request doors + windows
    print("\n3. Doors + Windows (Filtered)")
    print("-" * 70)
    status = adapter.get_physical_status(vin, components=['doors', 'windows'])
    print(f"   Doors Locked: {status.doors.lock_state if status.doors else 'N/A'}")
    if status.windows and status.windows.front_left:
        print(f"   Front Left Window: {'Open' if status.windows.front_left.open else 'Closed'}")
    else:
        print(f"   Windows: N/A")
    print(f"   Tyres: {status.tyres}")  # None
    print(f"   Lights: {status.lights}")  # None


def demo_energy_status():
    """Demonstrate get_energy_status() (vehicle-type-aware)"""
    print_section("⚡ ENERGY STATUS - Type-Aware Data", "=")
    
    adapter = TestAdapter()
    
    # Electric vehicle
    print("1. Electric Vehicle (ID7)")
    print("-" * 70)
    status = adapter.get_energy_status('WVWZZZED4SE003938')
    print(f"   Total Range: {status.range.total_km} km")
    print(f"   Electric Range: {status.range.electric_km} km")
    print(f"   Combustion Range: {status.range.combustion_km}")  # None
    if status.electric_drive:
        print(f"   Battery Level: {status.electric_drive.battery_level_percent}%")
        print(f"   Charging: {status.electric_drive.charging_state}")
        print(f"   Plug Connected: {status.electric_drive.plug_connected}")
    if status.combustion_drive:
        print(f"   Fuel Level: N/A (Electric)")
    
    # Combustion vehicle
    print("\n2. Combustion Vehicle (T7)")
    print("-" * 70)
    status = adapter.get_energy_status('WV2ZZZSTZNH009136')
    print(f"   Total Range: {status.range.total_km} km")
    print(f"   Electric Range: {status.range.electric_km}")  # None
    print(f"   Combustion Range: {status.range.combustion_km} km")
    if status.electric_drive:
        print(f"   Battery: N/A (Combustion)")
    if status.combustion_drive:
        print(f"   Fuel Level: {status.combustion_drive.fuel_level_percent}%")


def demo_climate_status():
    """Demonstrate get_climate_status()"""
    print_section("🌡️ CLIMATE STATUS - Unified Climate Info", "=")
    
    adapter = TestAdapter()
    vin = 'WVWZZZED4SE003938'
    
    status = adapter.get_climate_status(vin)
    
    print("Climatization:")
    print("-" * 70)
    if status.climatization:
        print(f"   State: {status.climatization.state}")
        print(f"   Active: {status.climatization.is_active}")
        print(f"   Target Temperature: {status.climatization.target_temperature_celsius}°C")
        print(f"   Time Remaining: {status.climatization.estimated_time_remaining_minutes} min")
        print(f"   External Power: {status.climatization.using_external_power}")
    
    print("\nWindow Heating:")
    print("-" * 70)
    if status.window_heating:
        print(f"   Front: {status.window_heating.front.state if status.window_heating.front else 'N/A'}")
        print(f"   Rear: {status.window_heating.rear.state if status.window_heating.rear else 'N/A'}")


def demo_comparison_old_vs_new():
    """Compare old vs new API approach"""
    print_section("📊 OLD vs NEW API - Comparison", "=")
    
    adapter = TestAdapter()
    vin = 'WVWZZZED4SE003938'
    
    print("OLD API (Phase 1+2): Multiple method calls")
    print("-" * 70)
    print("   ❌ battery = adapter.get_battery_status(vin)")
    print("   ❌ range = adapter.get_range_info(vin)")
    print("   ❌ doors = adapter.get_doors_state(vin)")
    print("   ❌ windows = adapter.get_windows_state(vin)")
    print("   ❌ tyres = adapter.get_tyres_state(vin)")
    print("   ❌ lights = adapter.get_lights_state(vin)")
    print("   ❌ climate = adapter.get_climatization_state(vin)")
    print("   ❌ window_heat = adapter.get_window_heating_state(vin)")
    print("   → 8 separate API calls")
    
    print("\nNEW API (Consolidated): Fewer, smarter calls")
    print("-" * 70)
    print("   ✅ vehicle = adapter.get_vehicle(vin, details='full')")
    print("   ✅ physical = adapter.get_physical_status(vin)")
    print("   ✅ energy = adapter.get_energy_status(vin)")
    print("   ✅ climate = adapter.get_climate_status(vin)")
    print("   → 4 logical groups, optional filtering")
    
    print("\nBenefits:")
    print("-" * 70)
    print("   • Fewer MCP tools (4 vs 10+)")
    print("   • Better organization (logical categories)")
    print("   • Flexible detail levels (BASIC/FULL)")
    print("   • Component filtering (request only what you need)")
    print("   • Easier to maintain and extend")


def main():
    print("\n" + "="*70)
    print("  CONSOLIDATED API DEMONSTRATION")
    print("  New architecture for better maintainability")
    print("="*70)
    
    demo_vehicle_info()
    demo_physical_status()
    demo_energy_status()
    demo_climate_status()
    demo_comparison_old_vs_new()
    
    print("\n" + "="*70)
    print("  Demo completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
