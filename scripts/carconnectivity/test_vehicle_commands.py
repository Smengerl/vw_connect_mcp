#!/usr/bin/env python3
"""
Direct test of vehicle commands using carconnectivity library (no adapter/MCP).

This script directly uses the carconnectivity library to send commands to vehicles
and test if remote control functions work.

IMPORTANT: This script will ACTUALLY execute commands on your vehicle!
Only use this for testing purposes and ensure your vehicle is in a safe location.

Usage:
    python scripts/test_vehicle_commands.py <vehicle_name_or_vin> [command]
    python scripts/test_vehicle_commands.py <config.json> <vehicle_name_or_vin> [command]
    
Available commands:
    unlock              - Unlock the vehicle (default)
    lock                - Lock the vehicle
    start_climatization - Start climate control
    stop_climatization  - Stop climate control
    start_charging      - Start charging
    stop_charging       - Stop charging
    honk_and_flash      - Honk and flash lights
    flash               - Flash lights only
    start_window_heating - Start window heating
    stop_window_heating  - Stop window heating
    
Examples:
    # Unlock the ID7 (default command)
    python scripts/test_vehicle_commands.py ID7
    python scripts/test_vehicle_commands.py src/config.json ID7
    
    # Lock the ID7
    python scripts/test_vehicle_commands.py ID7 lock
    python scripts/test_vehicle_commands.py src/config.json ID7 lock
    
    # Start climate control
    python scripts/test_vehicle_commands.py src/config.json ID7 start_climatization
"""

import sys
import json
import time
from pathlib import Path

# Import carconnectivity directly
from carconnectivity.carconnectivity import CarConnectivity


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def find_vehicle(garage, vehicle_identifier: str):
    """Find a vehicle by name or VIN."""
    vins = garage.list_vehicle_vins() if hasattr(garage, 'list_vehicle_vins') else []
    
    # Try to find by VIN first
    if vehicle_identifier in vins:
        return garage.get_vehicle(vehicle_identifier), vehicle_identifier
    
    # Try to find by name
    for vin in vins:
        vehicle = garage.get_vehicle(vin)
        if vehicle:
            name = vehicle.name.value if (vehicle.name and hasattr(vehicle.name, 'value')) else None
            if name and name.lower() == vehicle_identifier.lower():
                return vehicle, vin
    
    return None, None



# Import command classes at module level
from carconnectivity.command_impl import (
    LockUnlockCommand,
    ClimatizationStartStopCommand,
    ChargingStartStopCommand,
    HonkAndFlashCommand,
    WindowHeatingStartStopCommand,
)


# Unified command mapping: command_name -> (display_name, handler_function, command_enum, command_key, category)
COMMAND_REGISTRY = {}


def lock_vehicle(vehicle):
    """Lock the vehicle doors."""
    if not hasattr(vehicle, 'doors') or vehicle.doors is None or vehicle.doors.commands is None:
        print("❌ Vehicle does not support door commands")
        return False
    
    if not vehicle.doors.commands.contains_command("lock-unlock"):
        print("❌ Vehicle does not support lock/unlock command")
        return False
    
    try:
        vehicle.doors.commands.commands["lock-unlock"].value = LockUnlockCommand.Command.LOCK
        print("✅ Vehicle locked successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to lock vehicle: {e}")
        return False


def unlock_vehicle(vehicle):
    """Unlock the vehicle doors."""
    if not hasattr(vehicle, 'doors') or vehicle.doors is None or vehicle.doors.commands is None:
        print("❌ Vehicle does not support door commands")
        return False
    
    if not vehicle.doors.commands.contains_command("lock-unlock"):
        print("❌ Vehicle does not support lock/unlock command")
        return False
    
    try:
        vehicle.doors.commands.commands["lock-unlock"].value = LockUnlockCommand.Command.UNLOCK
        print("✅ Vehicle unlocked successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to unlock vehicle: {e}")
        return False


def start_climatization(vehicle):
    """Start climate control."""
    if not hasattr(vehicle, 'climatization') or vehicle.climatization is None or vehicle.climatization.commands is None:
        print("❌ Vehicle does not support climatization commands")
        return False
    
    if not vehicle.climatization.commands.contains_command("start-stop"):
        print("❌ Vehicle does not support climatization start/stop command")
        return False
    
    try:
        vehicle.climatization.commands.commands["start-stop"].value = ClimatizationStartStopCommand.Command.START
        print("✅ Climatization started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start climatization: {e}")
        return False


def stop_climatization(vehicle):
    """Stop climate control."""
    if not hasattr(vehicle, 'climatization') or vehicle.climatization is None or vehicle.climatization.commands is None:
        print("❌ Vehicle does not support climatization commands")
        return False
    
    if not vehicle.climatization.commands.contains_command("start-stop"):
        print("❌ Vehicle does not support climatization start/stop command")
        return False
    
    try:
        vehicle.climatization.commands.commands["start-stop"].value = ClimatizationStartStopCommand.Command.STOP
        print("✅ Climatization stopped successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to stop climatization: {e}")
        return False


def start_charging(vehicle):
    """Start charging."""
    if not hasattr(vehicle, 'charging') or vehicle.charging is None or vehicle.charging.commands is None:
        print("❌ Vehicle does not support charging commands")
        return False
    
    if not vehicle.charging.commands.contains_command("start-stop"):
        print("❌ Vehicle does not support charging start/stop command")
        return False
    
    try:
        vehicle.charging.commands.commands["start-stop"].value = ChargingStartStopCommand.Command.START
        print("✅ Charging started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start charging: {e}")
        return False


def stop_charging(vehicle):
    """Stop charging."""
    if not hasattr(vehicle, 'charging') or vehicle.charging is None or vehicle.charging.commands is None:
        print("❌ Vehicle does not support charging commands")
        return False
    
    if not vehicle.charging.commands.contains_command("start-stop"):
        print("❌ Vehicle does not support charging start/stop command")
        return False
    
    try:
        vehicle.charging.commands.commands["start-stop"].value = ChargingStartStopCommand.Command.STOP
        print("✅ Charging stopped successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to stop charging: {e}")
        return False


def flash_lights(vehicle):
    """Flash the vehicle lights."""
    if not hasattr(vehicle, 'controls') or vehicle.controls is None or vehicle.controls.commands is None:
        print("❌ Vehicle does not support control commands")
        return False
    
    if not vehicle.controls.commands.contains_command("honk-and-flash"):
        print("❌ Vehicle does not support honk/flash command")
        return False
    
    try:
        vehicle.controls.commands.commands["honk-and-flash"].value = HonkAndFlashCommand.Command.FLASH
        print("✅ Lights flashed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to flash lights: {e}")
        return False


def honk_and_flash(vehicle):
    """Honk and flash the vehicle."""
    if not hasattr(vehicle, 'controls') or vehicle.controls is None or vehicle.controls.commands is None:
        print("❌ Vehicle does not support control commands")
        return False
    
    if not vehicle.controls.commands.contains_command("honk-and-flash"):
        print("❌ Vehicle does not support honk/flash command")
        return False
    
    try:
        vehicle.controls.commands.commands["honk-and-flash"].value = HonkAndFlashCommand.Command.HONK_AND_FLASH
        print("✅ Honk and flash executed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to honk and flash: {e}")
        return False


def start_window_heating(vehicle):
    """Start window heating."""
    if not hasattr(vehicle, 'window_heating') or vehicle.window_heating is None or vehicle.window_heating.commands is None:
        print("❌ Vehicle does not support window heating commands")
        return False
    
    if not vehicle.window_heating.commands.contains_command("start-stop"):
        print("❌ Vehicle does not support window heating start/stop command")
        return False
    
    try:
        vehicle.window_heating.commands.commands["start-stop"].value = WindowHeatingStartStopCommand.Command.START
        print("✅ Window heating started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start window heating: {e}")
        return False


def stop_window_heating(vehicle):
    """Stop window heating."""
    if not hasattr(vehicle, 'window_heating') or vehicle.window_heating is None or vehicle.window_heating.commands is None:
        print("❌ Vehicle does not support window heating commands")
        return False
    
    if not vehicle.window_heating.commands.contains_command("start-stop"):
        print("❌ Vehicle does not support window heating start/stop command")
        return False
    
    try:
        vehicle.window_heating.commands.commands["start-stop"].value = WindowHeatingStartStopCommand.Command.STOP
        print("✅ Window heating stopped successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to stop window heating: {e}")
        return False


# Register all commands
COMMAND_REGISTRY = {
    "lock": ("lock doors", lock_vehicle),
    "unlock": ("unlock doors", unlock_vehicle),
    "start_climatization": ("start climate control", start_climatization),
    "stop_climatization": ("stop climate control", stop_climatization),
    "start_charging": ("start charging", start_charging),
    "stop_charging": ("stop charging", stop_charging),
    "flash": ("flash lights", flash_lights),
    "honk_and_flash": ("honk and flash", honk_and_flash),
    "start_window_heating": ("start window heating", start_window_heating),
    "stop_window_heating": ("stop window heating", stop_window_heating),
}





def execute_vehicle_command(car_conn, vehicle_identifier: str, command: str = "unlock", **kwargs):
    """Execute a command on a vehicle.
    
    Args:
        car_conn: CarConnectivity instance
        vehicle_identifier: Vehicle name or VIN
        command: Command to execute (unlock, lock, start_climatization, etc.)
    """
    
    # Check if command is registered
    if command not in COMMAND_REGISTRY:
        print(f"❌ Unknown command: {command}")
        print(f"\nAvailable commands: {', '.join(COMMAND_REGISTRY.keys())}")
        return False
    
    command_display, command_handler = COMMAND_REGISTRY[command]
    
    print("=" * 60)
    print(f"VEHICLE COMMAND TEST - {command.upper()}")
    print("=" * 60)
    print(f"Target vehicle: {vehicle_identifier}")
    print(f"Command: {command_display}")
    print()
    
    # Get the garage
    print("Step 1: Getting garage...")
    car_conn.fetch_all()
    garage = car_conn.get_garage()
    
    if garage is None:
        print("❌ No garage found")
        return False
    
    print("✅ Garage found")
    
    # Find the vehicle
    print(f"\nStep 2: Looking for vehicle '{vehicle_identifier}'...")
    vehicle, vin = find_vehicle(garage, vehicle_identifier)
    
    if vehicle is None:
        print(f"❌ Vehicle '{vehicle_identifier}' not found")
        print("\nAvailable vehicles:")
        vins = garage.list_vehicle_vins() if hasattr(garage, 'list_vehicle_vins') else []
        for v_vin in vins:
            v = garage.get_vehicle(v_vin)
            if v:
                name = v.name.value if (v.name and hasattr(v.name, 'value')) else "Unknown"
                print(f"  - {name} (VIN: {v_vin})")
        return False
    
    name = vehicle.name.value if (vehicle.name and hasattr(vehicle.name, 'value')) else "Unknown"
    model = vehicle.model.value if (vehicle.model and hasattr(vehicle.model, 'value')) else "Unknown"
    
    print(f"✅ Found vehicle: {name} ({model})")
    print(f"   VIN: {vin}")
    
    # Execute the command using the registered handler
    print(f"\nStep 3: Executing command '{command_display}'...")
    return command_handler(vehicle)






def main():
    # Parse arguments more robustly
    # Supports:
    # - script.py ID7                              -> default config, VIN=ID7, command=unlock
    # - script.py ID7 lock                         -> default config, VIN=ID7, command=lock
    # - script.py config.json ID7                  -> custom config, VIN=ID7, command=unlock
    # - script.py config.json ID7 lock             -> custom config, VIN=ID7, command=lock
    
    default_config = Path(__file__).parent.parent.parent / "src" / "config.json"
    config_path = None
    vehicle_identifier = None
    command = "unlock"  # Default command
    
    if len(sys.argv) == 1:
        # No arguments
        print("Error: Please provide a vehicle name or VIN")
        print()
        print("Usage:")
        print("  python scripts/test_vehicle_commands.py <vehicle_name_or_vin> [command]")
        print("  python scripts/test_vehicle_commands.py <config.json> <vehicle_name_or_vin> [command]")
        print()
        print("Available commands: unlock (default), lock, start_climatization, stop_climatization, honk_and_flash")
        print()
        print("Examples:")
        print("  python scripts/test_vehicle_commands.py ID7")
        print("  python scripts/test_vehicle_commands.py ID7 lock")
        print("  python scripts/test_vehicle_commands.py src/config.json ID7 start_climatization")
        sys.exit(1)
    
    elif len(sys.argv) == 2:
        # One argument - must be VIN (use default config and command)
        arg = sys.argv[1]
        
        # Check if it looks like a config file path
        if arg.endswith('.json') or '/' in arg:
            # Treat as config path - missing VIN
            print("Error: Please provide a vehicle name or VIN")
            print()
            print("Usage:")
            print(f"  python scripts/test_vehicle_commands.py {arg} <vehicle_name_or_vin> [command]")
            print()
            print("Example:")
            print(f"  python scripts/test_vehicle_commands.py {arg} ID7")
            print(f"  python scripts/test_vehicle_commands.py {arg} ID7 lock")
            sys.exit(1)
        else:
            # Treat as VIN, use default config and command
            config_path = default_config
            vehicle_identifier = arg
            command = "unlock"
    
    elif len(sys.argv) == 3:
        # Two arguments - could be:
        # 1. VIN + command (use default config)
        # 2. config + VIN (use default command)
        arg1 = sys.argv[1]
        arg2 = sys.argv[2]
        
        if arg1.endswith('.json') or '/' in arg1:
            # config.json + VIN
            config_path = Path(arg1)
            vehicle_identifier = arg2
            command = "unlock"
        else:
            # VIN + command
            config_path = default_config
            vehicle_identifier = arg1
            command = arg2
    
    else:
        # Three or more arguments - config + VIN + command
        config_path = Path(sys.argv[1])
        vehicle_identifier = sys.argv[2]
        command = sys.argv[3]
    

 
    print("=" * 60)
    print("CARCONNECTIVITY DIRECT COMMAND TEST")
    print("=" * 60)
    print(f"Config: {config_path}")
    print(f"Vehicle: {vehicle_identifier}")
    print(f"Command: {command}")
    print()
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
        # Execute command
        success = execute_vehicle_command(car_conn, vehicle_identifier, command)
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
        
    finally:
        # Cleanup
        print("\nCleaning up...")
        if hasattr(car_conn, 'shutdown'):
            car_conn.shutdown()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Aborted by user")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ Config file not found: {e}")
        print("Usage: python scripts/test_vehicle_commands.py [config.json] <vehicle_name_or_vin>")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
