#!/usr/bin/env python3
"""Send commands to VW vehicles using CarConnectivityAdapter.

This script uses the CarConnectivityAdapter to execute commands on vehicles.

⚠️ WARNING: This will ACTUALLY execute commands on your vehicle!
Only use for testing in safe conditions.

Usage:
    python scripts/vehicle_command.py <vehicle_id> <command> [options]
    ./scripts/vehicle_command.sh <vehicle_id> <command> [options]

Available Commands:
    Lock/Unlock:
        lock                    Lock the vehicle
        unlock                  Unlock the vehicle
    
    Climatization:
        start_climatization     Start climate control
        stop_climatization      Stop climate control
    
    Charging (BEV/PHEV only):
        start_charging          Start charging
        stop_charging           Stop charging
    
    Lights/Horn:
        flash_lights            Flash lights only
        honk_and_flash          Honk and flash lights
    
    Window Heating:
        start_window_heating    Start window heating
        stop_window_heating     Stop window heating

Examples:
    ./scripts/vehicle_command.sh ID7 lock
    ./scripts/vehicle_command.sh Golf unlock
    ./scripts/vehicle_command.sh ID7 start_climatization
    ./scripts/vehicle_command.sh ID7 start_charging
    ./scripts/vehicle_command.sh Golf flash_lights
"""

import sys
import json
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter


# Command registry: maps command names to adapter methods
COMMANDS = {
    # Lock/Unlock
    "lock": "lock_vehicle",
    "unlock": "unlock_vehicle",
    
    # Climatization
    "start_climatization": "start_climatization",
    "stop_climatization": "stop_climatization",
    
    # Charging
    "start_charging": "start_charging",
    "stop_charging": "stop_charging",
    
    # Lights/Horn
    "flash_lights": "flash_lights",
    "honk_and_flash": "honk_and_flash",
    
    # Window Heating
    "start_window_heating": "start_window_heating",
    "stop_window_heating": "stop_window_heating",
}


def print_usage():
    """Print usage information."""
    print("Usage: vehicle_command.py <vehicle_id> <command>")
    print()
    print("Available commands:")
    print("  Lock/Unlock:")
    print("    lock, unlock")
    print()
    print("  Climatization:")
    print("    start_climatization, stop_climatization")
    print()
    print("  Charging (BEV/PHEV only):")
    print("    start_charging, stop_charging")
    print()
    print("  Lights/Horn:")
    print("    flash_lights, honk_and_flash")
    print()
    print("  Window Heating:")
    print("    start_window_heating, stop_window_heating")
    print()
    print("Examples:")
    print("  ./scripts/vehicle_command.sh ID7 lock")
    print("  ./scripts/vehicle_command.sh Golf start_climatization")
    print()


def execute_command(vehicle_id: str, command: str) -> bool:
    """Execute a command on a vehicle.
    
    Args:
        vehicle_id: Vehicle name or VIN
        command: Command to execute
        
    Returns:
        True if successful, False otherwise
    """
    # Validate command
    if command not in COMMANDS:
        print(f"❌ Unknown command: {command}")
        print()
        print(f"Available commands: {', '.join(COMMANDS.keys())}")
        print()
        print("Run with --help for more information")
        return False
    
    method_name = COMMANDS[command]
    
    print("=" * 70)
    print(f"VEHICLE COMMAND: {command.upper()}")
    print("=" * 70)
    print(f"Vehicle: {vehicle_id}")
    print()
    
    # Initialize adapter
    print("Step 1: Initializing adapter...")
    config_path = Path(__file__).parent.parent / "src" / "config.json"
    tokenstore_path = Path("/tmp/tokenstore")
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print()
        print("Please create src/config.json with your VW credentials.")
        return False
    
    try:
        adapter = CarConnectivityAdapter(
            config_path=str(config_path),
            tokenstore_file=str(tokenstore_path)
        )
        print("✅ Adapter initialized")
    except Exception as e:
        print(f"❌ Failed to initialize adapter: {e}")
        return False
    
    # List vehicles to verify vehicle_id
    print()
    print("Step 2: Finding vehicle...")
    try:
        vehicles = adapter.list_vehicles()
        
        # Check if vehicle exists
        vehicle_found = False
        for v in vehicles:
            if v.vin == vehicle_id or (v.name and v.name.lower() == vehicle_id.lower()):
                vehicle_found = True
                print(f"✅ Found vehicle: {v.name or v.vin} ({v.model})")
                break
        
        if not vehicle_found:
            print(f"❌ Vehicle '{vehicle_id}' not found")
            print()
            print("Available vehicles:")
            for v in vehicles:
                print(f"  - {v.name or v.vin} ({v.model})")
            return False
            
    except Exception as e:
        print(f"❌ Failed to list vehicles: {e}")
        return False
    
    # Execute command
    print()
    print(f"Step 3: Executing command '{command}'...")
    try:
        method = getattr(adapter, method_name)
        result = method(vehicle_id)
        
        # Check result
        if isinstance(result, dict):
            if result.get("success"):
                print(f"✅ {result.get('message', 'Command executed successfully')}")
                return True
            else:
                print(f"❌ {result.get('error', 'Command failed')}")
                return False
        else:
            print(f"⚠️  Unexpected result type: {type(result)}")
            print(f"   Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to execute command: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    # Parse arguments
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print_usage()
        sys.exit(0)
    
    if len(sys.argv) < 3:
        print("❌ Error: Missing arguments")
        print()
        print_usage()
        sys.exit(1)
    
    vehicle_id = sys.argv[1]
    command = sys.argv[2]
    
    # Execute command
    success = execute_command(vehicle_id, command)
    
    print()
    print("=" * 70)
    if success:
        print("✅ COMMAND COMPLETED SUCCESSFULLY")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ COMMAND FAILED")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("❌ Aborted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
