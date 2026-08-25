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
    
    # 3. Demonstrate energy status lookup with different identifiers
    print("\n3. Access Vehicle Data Using Different Identifiers")
    print("-" * 70)

    # 3a. By Name
    print("   A. Access by Name: 'ID7'")
    energy = adapter.get_energy_status('ID7')
    print(f"      Battery: {energy.electric.battery_level_percent}%")
    print(f"      Range: {energy.range.total_km} km")
    print()

    # 3b. By License Plate
    print("   B. Access by License Plate: 'M-XY 5678'")
    energy = adapter.get_energy_status('M-XY 5678')
    print(f"      Battery: {energy.electric.battery_level_percent}%")
    print(f"      Range: {energy.range.total_km} km")
    print()

    # 3c. By VIN (backwards compatibility)
    print("   C. Access by VIN: 'WVWZZZED4SE003938'")
    energy = adapter.get_energy_status('WVWZZZED4SE003938')
    print(f"      Battery: {energy.electric.battery_level_percent}%")
    print(f"      Range: {energy.range.total_km} km")
    print()

    # 4. All three methods return identical results
    print("\n4. Verification: All Methods Return Same Data")
    print("-" * 70)
    by_name = adapter.get_energy_status('ID7')
    by_plate = adapter.get_energy_status('M-XY 5678')
    by_vin = adapter.get_energy_status('WVWZZZED4SE003938')

    print(f"   By Name:          {by_name.electric.battery_level_percent}% / {by_name.range.total_km} km")
    print(f"   By License Plate: {by_plate.electric.battery_level_percent}% / {by_plate.range.total_km} km")
    print(f"   By VIN:           {by_vin.electric.battery_level_percent}% / {by_vin.range.total_km} km")
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
        ("How much battery does my ID7 have?", "ID7"),
        ("Is my ID7 charging?", "ID7"),
        ("What's the range of M-XY 5678?", "M-XY 5678"),
    ]

    for i, (query, identifier) in enumerate(use_cases, 1):
        print(f"   Use Case {i}: \"{query}\"")
        data = adapter.get_energy_status(identifier)
        if data.electric:
            charging = data.electric.charging
            status = "Charging" if charging and charging.is_charging else "Not charging"
            print(f"      → Battery: {data.electric.battery_level_percent}%, "
                  f"Range: {data.range.total_km} km, {status}")
        else:
            # Tibber's vehicle integration is EV-only (see ARCHITECTURE.md),
            # so `electric` is always populated in practice -- this branch
            # only exists because the type (Optional[ElectricDriveInfo])
            # still technically allows None.
            print("      → No energy data available for this vehicle")
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
