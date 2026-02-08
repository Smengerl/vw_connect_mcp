#!/usr/bin/env python3
"""
Direct check of license plate using carconnectivity library (no adapter/MCP).

This script directly uses the carconnectivity library to fetch vehicle data
and check if license plates are available.

IMPORTANT NOTE: As of February 2026, the VW WeConnect API does NOT provide
license plate information. This is a current limitation of the VW API itself,
not a limitation of this library or script. The API returns None/null for
the license_plate field for all vehicles.

This script is provided for testing and demonstration purposes, and to verify
when/if VW adds license plate data to their API in the future.

Usage:
    python scripts/demo_check_license.py [config.json]
"""

import sys
import json
from pathlib import Path

# Import carconnectivity directly
from carconnectivity.carconnectivity import CarConnectivity

def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    # Get config path
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = Path(__file__).parent.parent / "src" / "config.json"
    
    print("=" * 60)
    print("LICENSE PLATE CHECK (direct carconnectivity API)")
    print("=" * 60)
    print(f"Config: {config_path}")
    print("Connecting to VW API...")
    print()
    
    # Load config
    config = load_config(str(config_path))
    
    # Create CarConnectivity instance
    # CarConnectivity expects the config dict directly (already has 'carConnectivity' key)
    car_conn = CarConnectivity(
        config=config,
        tokenstore_file="/tmp/tokenstore_direct_check"
    )
    
    try:
        # Get the garage (collection of vehicles)
        print("Fetching garage...")
        car_conn.fetch_all()
        garage = car_conn.get_garage()
        
        if garage is None:
            print("❌ No garage found (no vehicles registered or API error)")
            print("\nPossible causes:")
            print("  - VW API is currently unavailable")
            print("  - Invalid credentials in config.json")
            print("  - No vehicles registered in your VW account")
            return
        
        # Get all VINs
        vins = garage.list_vehicle_vins() if hasattr(garage, 'list_vehicle_vins') else []
        
        if not vins:
            print("❌ No vehicles found in garage")
            print("\nTip: The VW API might be temporarily unavailable.")
            print("     Try again later or check your VW We Connect app.")
            return
        
        print(f"Found {len(vins)} vehicle(s):\n")
        
        for vin in vins:
            # Get vehicle object
            vehicle = garage.get_vehicle(vin)
            if not vehicle:
                print(f"⚠️  Could not get details for VIN: {vin}")
                continue
            
            # Get basic info (handle None values)
            name = vehicle.name.value if (vehicle.name is not None and hasattr(vehicle.name, 'value')) else "Unknown"
            model = vehicle.model.value if (vehicle.model is not None and hasattr(vehicle.model, 'value')) else "Unknown"
            license_plate = vehicle.license_plate.value if (vehicle.license_plate is not None and hasattr(vehicle.license_plate, 'value')) else None
            
            # Print vehicle info
            print(f"Vehicle: {name}")
            print(f"  Model:         {model}")
            print(f"  VIN:           {vin}")
            print(f"  License Plate: {license_plate or '❌ NOT AVAILABLE (VW API limitation)'}")
            
            # Check for ID models
            if name and ("ID" in name or "ID7" in name or (model and "ID.7" in model)):
                print(f"  ⚡ This is an electric ID model!")
                if license_plate:
                    print(f"  ✅ License plate IS available: {license_plate}")
                else:
                    print(f"  ❌ License plate is NOT available (VW API does not provide this data)")
            
            # Debug: Show some available attributes
            attrs = [attr for attr in dir(vehicle) if not attr.startswith('_')]
            print(f"  Available attributes ({len(attrs)} total): {', '.join(attrs[:8])}...")
            print()
        
        print("=" * 60)
        print("ℹ️  NOTE: VW WeConnect API Limitation")
        print("=" * 60)
        print("The VW API currently does NOT provide license plate data.")
        print("This is a limitation of Volkswagen's API, not this library.")
        print("License plates shown in test data are for demonstration only.")
        print("=" * 60)
        
        print("=" * 60)
        print("CHECK COMPLETE")
        print("=" * 60)
        
    finally:
        # Cleanup
        if hasattr(car_conn, 'disconnect'):
            car_conn.disconnect()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ Config file not found: {e}")
        print("Usage: python scripts/demo_check_license.py [path/to/config.json]")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
