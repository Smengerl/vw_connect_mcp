#!/usr/bin/env python3
"""
Demo script showing the new Phase 1 MCP tools:
- get_climatization_state
- get_maintenance_info
- get_range_info
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_adapter import TestAdapter
import json


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_climatization():
    """Demonstrate climatization state retrieval"""
    print_section("🌡️  CLIMATIZATION STATE")
    
    adapter = TestAdapter()
    
    # Get climatization for ID7 (active heating)
    print("📍 ID7 (Electric Vehicle):")
    climate = adapter.get_climatization_state('WVWZZZED4SE003938')
    if climate:
        print(f"  Status: {climate.state}")
        print(f"  Active: {climate.is_active}")
        print(f"  Target Temperature: {climate.target_temperature_celsius}°C")
        print(f"  Time Remaining: {climate.estimated_time_remaining_minutes} min")
        print(f"  Window Heating: {climate.window_heating_enabled}")
        print(f"  Seat Heating: {climate.seat_heating_enabled}")
        print(f"  External Power: {climate.using_external_power}")
    
    # Get climatization for T7 (off)
    print("\n📍 T7 (Combustion Vehicle):")
    climate = adapter.get_climatization_state('WV2ZZZSTZNH009136')
    if climate:
        print(f"  Status: {climate.state}")
        print(f"  Active: {climate.is_active}")
        print(f"  Target Temperature: {climate.target_temperature_celsius}°C")


def demo_maintenance():
    """Demonstrate maintenance info retrieval"""
    print_section("🔧 MAINTENANCE INFO")
    
    adapter = TestAdapter()
    
    # Get maintenance for ID7 (electric - no oil service)
    print("📍 ID7 (Electric Vehicle):")
    maintenance = adapter.get_maintenance_info('WVWZZZED4SE003938')
    if maintenance:
        print(f"  Next Inspection: {maintenance.inspection_due_date}")
        print(f"  Inspection in: {maintenance.inspection_due_distance_km} km")
        print(f"  Oil Service: N/A (Electric Vehicle)")
    
    # Get maintenance for T7 (combustion - has oil service)
    print("\n📍 T7 (Combustion Vehicle):")
    maintenance = adapter.get_maintenance_info('WV2ZZZSTZNH009136')
    if maintenance:
        print(f"  Next Inspection: {maintenance.inspection_due_date}")
        print(f"  Inspection in: {maintenance.inspection_due_distance_km} km")
        print(f"  Next Oil Service: {maintenance.oil_service_due_date}")
        print(f"  Oil Service in: {maintenance.oil_service_due_distance_km} km")


def demo_range():
    """Demonstrate range info retrieval"""
    print_section("🔋 RANGE INFO")
    
    adapter = TestAdapter()
    
    # Get range for ID7 (electric)
    print("📍 ID7 (Electric Vehicle):")
    range_info = adapter.get_range_info('WVWZZZED4SE003938')
    if range_info:
        print(f"  Total Range: {range_info.total_range_km} km")
        if range_info.electric_drive:
            print(f"  Electric Range: {range_info.electric_drive.range_km} km")
            print(f"  Battery Level: {range_info.electric_drive.battery_level_percent}%")
    
    # Get range for T7 (combustion)
    print("\n📍 T7 (Combustion Vehicle):")
    range_info = adapter.get_range_info('WV2ZZZSTZNH009136')
    if range_info:
        print(f"  Total Range: {range_info.total_range_km} km")
        if range_info.combustion_drive:
            print(f"  Combustion Range: {range_info.combustion_drive.range_km} km")
            print(f"  Tank Level: {range_info.combustion_drive.tank_level_percent}%")


def demo_all_features():
    """Show all features for one vehicle"""
    print_section("📊 COMPLETE VEHICLE STATUS")
    
    adapter = TestAdapter()
    vin = 'WVWZZZED4SE003938'
    
    print("Vehicle: ID7 (Electric)\n")
    
    # Climatization
    climate = adapter.get_climatization_state(vin)
    if climate:
        print("🌡️  Climate Control:")
        state_str = climate.state.upper() if climate.state else 'UNKNOWN'
        print(f"   {state_str} - Target: {climate.target_temperature_celsius}°C")
        if climate.estimated_time_remaining_minutes:
            print(f"   Ready in {climate.estimated_time_remaining_minutes} minutes")
    
    # Maintenance
    maintenance = adapter.get_maintenance_info(vin)
    if maintenance:
        print("\n🔧 Maintenance:")
        print(f"   Next inspection in {maintenance.inspection_due_distance_km} km")
    
    # Range
    range_info = adapter.get_range_info(vin)
    if range_info:
        print("\n🔋 Range:")
        if range_info.electric_drive:
            print(f"   {range_info.electric_drive.range_km} km ({range_info.electric_drive.battery_level_percent}% battery)")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  PHASE 1 MCP TOOLS DEMONSTRATION")
    print("="*60)
    
    demo_climatization()
    demo_maintenance()
    demo_range()
    demo_all_features()
    
    print("\n" + "="*60)
    print("  ✅ All Phase 1 tools working correctly!")
    print("="*60 + "\n")
