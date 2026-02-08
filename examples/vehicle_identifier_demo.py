#!/usr/bin/env python3
"""
Demo: Vehicle Identification with VIN, Name, and License Plate

This script demonstrates the flexible vehicle identification system that allows
accessing vehicles by VIN, name, or license plate.
"""

from tests.test_adapter import TestAdapter


def main():
    print("=" * 70)
    print("Vehicle Identifier Resolution Demo")
    print("=" * 70)
    print()
    
    adapter = TestAdapter()
    
    # 1. List all vehicles (now includes license plates)
    print("1. List All Vehicles (with License Plates)")
    print("-" * 70)
    vehicles = adapter.list_vehicles()
    for v in vehicles:
        print(f"   🚗 {v.name} ({v.model})")
        print(f"      VIN: {v.vin}")
        print(f"      License Plate: {v.license_plate}")
        print()
    
    # 2. Demonstrate resolution priority
    print("\n2. Identifier Resolution (Priority: Name > VIN > License Plate)")
    print("-" * 70)
    
    test_identifiers = [
        ('ID7', 'Name (exact match)'),
        ('id7', 'Name (case-insensitive)'),
        ('ID', 'Name (partial match)'),
        ('WVWZZZED4SE003938', 'VIN (exact match)'),
        ('wvwzzzed4se003938', 'VIN (case-insensitive)'),
        ('M-XY 5678', 'License Plate (exact match)'),
        ('m-xy 5678', 'License Plate (case-insensitive)'),
        ('  ID7  ', 'Name (with whitespace)'),
        ('UNKNOWN', 'Non-existent vehicle'),
    ]
    
    for identifier, description in test_identifiers:
        vin = adapter.resolve_vehicle_id(identifier)
        if vin:
            vehicle = adapter.get_vehicle(vin)
            print(f"   ✅ '{identifier}' ({description})")
            print(f"      → {vehicle.name} ({vin})")
        else:
            print(f"   ❌ '{identifier}' ({description})")
            print(f"      → Not found")
        print()
    
    # 3. Demonstrate tool usage with different identifiers
    print("\n3. Access Vehicle Data Using Different Identifiers")
    print("-" * 70)
    
    # 3a. By Name
    print("   A. Access by Name: 'ID7'")
    battery = adapter.get_battery_status('ID7')
    position = adapter.get_position('ID7')
    print(f"      Battery: {battery.battery_level_percent}%")
    print(f"      Range: {battery.range_km} km")
    print(f"      Position: {position.latitude:.4f}°N, {position.longitude:.4f}°E")
    print()
    
    # 3b. By License Plate
    print("   B. Access by License Plate: 'M-XY 5678'")
    battery = adapter.get_battery_status('M-XY 5678')
    position = adapter.get_position('M-XY 5678')
    print(f"      Battery: {battery.battery_level_percent}%")
    print(f"      Range: {battery.range_km} km")
    print(f"      Position: {position.latitude:.4f}°N, {position.longitude:.4f}°E")
    print()
    
    # 3c. By VIN (backwards compatibility)
    print("   C. Access by VIN: 'WVWZZZED4SE003938'")
    battery = adapter.get_battery_status('WVWZZZED4SE003938')
    position = adapter.get_position('WVWZZZED4SE003938')
    print(f"      Battery: {battery.battery_level_percent}%")
    print(f"      Range: {battery.range_km} km")
    print(f"      Position: {position.latitude:.4f}°N, {position.longitude:.4f}°E")
    print()
    
    # 4. All three methods return identical results
    print("\n4. Verification: All Methods Return Same Data")
    print("-" * 70)
    by_name = adapter.get_battery_status('ID7')
    by_plate = adapter.get_battery_status('M-XY 5678')
    by_vin = adapter.get_battery_status('WVWZZZED4SE003938')
    
    print(f"   By Name:          {by_name.battery_level_percent}% / {by_name.range_km} km")
    print(f"   By License Plate: {by_plate.battery_level_percent}% / {by_plate.range_km} km")
    print(f"   By VIN:           {by_vin.battery_level_percent}% / {by_vin.range_km} km")
    print()
    
    if by_name == by_plate == by_vin:
        print("   ✅ All methods return identical data!")
    else:
        print("   ❌ Data mismatch!")
    
    # 5. Real-world use cases
    print("\n5. Real-World AI Assistant Use Cases")
    print("-" * 70)
    print()
    
    use_cases = [
        ("How much battery does my ID7 have?", "ID7", "battery_status"),
        ("Where is the car with plate M-AB 1234?", "M-AB 1234", "position"),
        ("Is my T7 charging?", "T7", "charging_state"),
        ("What's the range of M-XY 5678?", "M-XY 5678", "range_info"),
    ]
    
    for i, (query, identifier, tool) in enumerate(use_cases, 1):
        print(f"   Use Case {i}: \"{query}\"")
        
        if tool == "battery_status":
            data = adapter.get_battery_status(identifier)
            print(f"      → Battery: {data.battery_level_percent}%, Range: {data.range_km} km")
        elif tool == "position":
            data = adapter.get_position(identifier)
            print(f"      → Position: {data.latitude:.4f}°N, {data.longitude:.4f}°E")
        elif tool == "charging_state":
            data = adapter.get_charging_state(identifier)
            if data:
                status = "Charging" if data.is_charging else "Not charging"
                print(f"      → {status} ({data.current_soc_percent}%)")
            else:
                print(f"      → Not an electric vehicle")
        elif tool == "range_info":
            data = adapter.get_range_info(identifier)
            print(f"      → Total Range: {data.total_range_km} km")
        print()
    
    print("=" * 70)
    print("Summary:")
    print("  • Vehicles can be identified by Name, VIN, or License Plate")
    print("  • Name has highest priority (partial match, case-insensitive)")
    print("  • VIN is second priority (exact match, case-insensitive)")
    print("  • License Plate is third priority (exact match, case-insensitive)")
    print("  • All tools support all three identifier types")
    print("  • Backwards compatible with VIN-only code")
    print("=" * 70)


if __name__ == "__main__":
    main()
