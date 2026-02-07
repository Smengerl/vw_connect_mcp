#!/usr/bin/env python3
"""
Example script demonstrating the get_vehicle_type MCP tool.

This shows how to use the new vehicle type functionality to identify
whether a vehicle is electric, combustion, or hybrid.
"""

from tests.test_adapter import TestAdapter
from weconnect_mcp.server.mcp_server import get_server


def main():
    """Demonstrate vehicle type detection."""
    
    # Create adapter with test data
    adapter = TestAdapter()
    
    print("=" * 60)
    print("Vehicle Type Detection Example")
    print("=" * 60)
    print()
    
    # List all vehicles
    vehicles = adapter.list_vehicles()
    print(f"Found {len(vehicles)} vehicle(s):\n")
    
    for vehicle in vehicles:
        print(f"Vehicle: {vehicle.name} ({vehicle.model})")
        print(f"  VIN: {vehicle.vin}")
        
        # Get vehicle type using the new method
        vehicle_type = adapter.get_vehicle_type(vehicle.vin)
        
        if vehicle_type:
            print(f"  Type: {vehicle_type.upper()}")
            
            # Provide human-friendly description
            type_descriptions = {
                'electric': 'Battery Electric Vehicle (BEV) - Zero emissions, electric only',
                'combustion': 'Internal Combustion Engine - Traditional gasoline/diesel',
                'hybrid': 'Hybrid Electric Vehicle (HEV/PHEV) - Combines electric and combustion',
                'plugin_hybrid': 'Plug-in Hybrid - Can charge from external source',
            }
            
            description = type_descriptions.get(vehicle_type, 'Unknown vehicle type')
            print(f"  Description: {description}")
        else:
            print(f"  Type: UNKNOWN")
        
        print()
    
    print("=" * 60)
    print("\nMCP Tool Usage Example:")
    print("=" * 60)
    print("\nWhen using Claude with the MCP server, you can ask:")
    print('  - "What type of vehicle is the T7?"')
    print('  - "Is the ID7 electric or combustion?"')
    print('  - "Which of my vehicles are electric?"')
    print()
    print("Claude will call get_vehicle_type(vehicle_id) to answer.")


if __name__ == "__main__":
    main()
