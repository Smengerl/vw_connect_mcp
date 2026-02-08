#!/usr/bin/env python3
"""
Demo: License Plate Support

This script demonstrates the license_plate field that is now available
in both VehicleListItem and VehicleModel.

Recent fix: license_plate was only available in list_vehicles() but missing
from get_vehicle(). Now it's consistently available in both methods.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_adapter import TestAdapter
from weconnect_mcp.adapter.abstract_adapter import VehicleDetailLevel


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_list_vehicles_with_plates():
    """Show license plates in vehicle listing"""
    print_section("📋 LIST VEHICLES - With License Plates")
    
    adapter = TestAdapter()
    vehicles = adapter.list_vehicles()
    
    print(f"Found {len(vehicles)} vehicles:\n")
    
    for i, vehicle in enumerate(vehicles, 1):
        print(f"{i}. {vehicle.name} ({vehicle.model})")
        print(f"   VIN: {vehicle.vin}")
        print(f"   License Plate: {vehicle.license_plate}")
        print()


def demo_get_vehicle_with_plate():
    """Show license plate in detailed vehicle info"""
    print_section("🚗 GET VEHICLE - License Plate Included")
    
    adapter = TestAdapter()
    
    # BASIC detail level
    print("1. BASIC Detail Level")
    print("-" * 70)
    vehicle = adapter.get_vehicle('WV2ZZZSTZNH009136', details=VehicleDetailLevel.BASIC)
    print(f"   Name: {vehicle.name}")
    print(f"   Model: {vehicle.model}")
    print(f"   License Plate: {vehicle.license_plate}")  # ✅ Now available!
    print()
    
    # FULL detail level
    print("2. FULL Detail Level")
    print("-" * 70)
    vehicle = adapter.get_vehicle('WVWZZZED4SE003938', details=VehicleDetailLevel.FULL)
    print(f"   Name: {vehicle.name}")
    print(f"   Model: {vehicle.model}")
    print(f"   License Plate: {vehicle.license_plate}")  # ✅ Now available!
    print(f"   Odometer: {vehicle.odometer} km")
    print(f"   State: {vehicle.state}")
    print()


def demo_vehicle_identification_by_plate():
    """Demonstrate identifying vehicles by license plate"""
    print_section("🔍 VEHICLE IDENTIFICATION - By License Plate")
    
    adapter = TestAdapter()
    
    # You can now use license plate as identifier
    test_plates = [
        'M-AB 1234',  # T7
        'M-XY 5678',  # ID7
        'm-ab 1234',  # Case-insensitive
    ]
    
    for plate in test_plates:
        vin = adapter.resolve_vehicle_id(plate)
        if vin:
            vehicle = adapter.get_vehicle(vin)
            print(f"   License Plate: '{plate}'")
            print(f"   → Found: {vehicle.name} ({vehicle.model})")
            print(f"   → VIN: {vin}")
        else:
            print(f"   License Plate: '{plate}'")
            print(f"   → Not found")
        print()


def demo_consistency_check():
    """Verify license plate consistency between list and get"""
    print_section("✅ CONSISTENCY CHECK - list_vehicles() vs get_vehicle()")
    
    adapter = TestAdapter()
    
    # Get all vehicles from list
    vehicles_list = adapter.list_vehicles()
    
    print("Comparing license plates from both methods:\n")
    
    for vehicle_item in vehicles_list:
        # Get detailed info
        vehicle_full = adapter.get_vehicle(vehicle_item.vin)
        
        list_plate = vehicle_item.license_plate
        get_plate = vehicle_full.license_plate
        
        match = "✅" if list_plate == get_plate else "❌"
        
        print(f"{match} {vehicle_item.name}:")
        print(f"   list_vehicles(): {list_plate}")
        print(f"   get_vehicle():   {get_plate}")
        
        if list_plate == get_plate:
            print(f"   → Consistent!")
        else:
            print(f"   → MISMATCH!")
        print()


def demo_before_and_after():
    """Show what changed with the license_plate fix"""
    print_section("📝 BEFORE vs AFTER - The Fix")
    
    print("BEFORE (Bug):")
    print("-" * 70)
    print("  ❌ VehicleModel did NOT have license_plate field")
    print("  ❌ get_vehicle() did NOT return license_plate")
    print("  ✅ VehicleListItem had license_plate field")
    print("  ✅ list_vehicles() returned license_plate")
    print()
    print("  Result: Inconsistent API - plate only available in listing")
    print()
    
    print("AFTER (Fixed):")
    print("-" * 70)
    print("  ✅ VehicleModel NOW has license_plate field")
    print("  ✅ get_vehicle() NOW returns license_plate")
    print("  ✅ VehicleListItem still has license_plate field")
    print("  ✅ list_vehicles() still returns license_plate")
    print()
    print("  Result: Consistent API - plate available everywhere")
    print()
    
    print("Files Changed:")
    print("-" * 70)
    print("  1. src/weconnect_mcp/adapter/abstract_adapter.py")
    print("     → Added license_plate field to VehicleModel")
    print()
    print("  2. src/weconnect_mcp/adapter/carconnectivity_adapter.py")
    print("     → get_vehicle() now reads and returns license_plate")
    print()
    print("  3. tests/test_adapter.py")
    print("     → TestAdapter updated to include license_plate in test data")


def demo_use_cases():
    """Show practical use cases for license plate"""
    print_section("💡 USE CASES - Why License Plate Matters")
    
    print("1. User-Friendly Vehicle Selection")
    print("-" * 70)
    print("   Users can identify their car by license plate instead of VIN:")
    print('   "Show me the battery status of M-AB 1234"')
    print('   → Much easier to remember than VIN!')
    print()
    
    print("2. Multi-Vehicle Households")
    print("-" * 70)
    print("   Family with multiple cars:")
    print("   • M-AB 1234: Dad's T7 Transporter")
    print("   • M-XY 5678: Mom's ID7 Electric")
    print("   → Easy to distinguish vehicles")
    print()
    
    print("3. Fleet Management")
    print("-" * 70)
    print("   Company managing multiple vehicles:")
    print("   • Track vehicles by license plate (publicly visible)")
    print("   • Cross-reference with internal databases")
    print("   • Generate reports using plate numbers")
    print()
    
    print("4. Parking & Location Services")
    print("-" * 70)
    print('   "Where is my car with plate M-AB 1234?"')
    print("   → Get position by license plate")
    print("   → More natural than using VIN")


def main():
    print("\n" + "="*70)
    print("  LICENSE PLATE SUPPORT DEMONSTRATION")
    print("  Now available in both list_vehicles() and get_vehicle()")
    print("="*70)
    
    demo_list_vehicles_with_plates()
    demo_get_vehicle_with_plate()
    demo_vehicle_identification_by_plate()
    demo_consistency_check()
    demo_before_and_after()
    demo_use_cases()
    
    print("\n" + "="*70)
    print("  Demo completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
