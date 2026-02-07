#!/usr/bin/env python3
"""
Demo script showing the charging state detection functionality.

This script demonstrates how to:
1. List all vehicles
2. Check which vehicles support charging
3. Get detailed charging information for electric/hybrid vehicles
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_adapter import TestAdapter
from weconnect_mcp.server.mcp_server import get_server


def format_time(minutes):
    """Format minutes as HH:MM"""
    if minutes is None:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}min"


def format_charging_state(charging):
    """Format charging state for display"""
    if not charging:
        return "Not available (not an electric vehicle)"
    
    lines = []
    if charging.is_charging:
        lines.append(f"  ⚡ CHARGING at {charging.charging_power_kw} kW")
        if charging.remaining_time_minutes:
            lines.append(f"  ⏱️  Estimated completion: {format_time(charging.remaining_time_minutes)}")
    elif charging.is_plugged_in:
        lines.append(f"  🔌 PLUGGED IN but not charging")
    else:
        lines.append(f"  ⭕ NOT PLUGGED IN")
    
    lines.append(f"  🔋 Battery: {charging.current_soc_percent}% (target: {charging.target_soc_percent}%)")
    lines.append(f"  📊 State: {charging.charging_state}")
    if charging.charge_mode:
        lines.append(f"  ⚙️  Mode: {charging.charge_mode}")
    
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Charging State Detection Example")
    print("=" * 60)
    print()
    
    # Create adapter and list vehicles
    adapter = TestAdapter()
    vehicles = adapter.list_vehicles()
    
    print(f"Found {len(vehicles)} vehicle(s):\n")
    
    for v in vehicles:
        print(f"Vehicle: {v.name} ({v.model})")
        print(f"  VIN: {v.vin}")
        
        # Get vehicle type
        vehicle_type = adapter.get_vehicle_type(v.vin)
        print(f"  Type: {vehicle_type.upper() if vehicle_type else 'UNKNOWN'}")
        
        # Get charging state
        charging = adapter.get_charging_state(v.vin)
        print()
        print(format_charging_state(charging))
        print()
    
    print("=" * 60)
    print()
    print("MCP Tool Usage Example:")
    print("=" * 60)
    print()
    print("When using Claude with the MCP server, you can ask:")
    print("  - \"Is the ID7 currently charging?\"")
    print("  - \"When will the ID7 finish charging?\"")
    print("  - \"What's the battery level of my electric cars?\"")
    print("  - \"Show me the charging status of all my vehicles\"")
    print()
    print("Claude will call get_charging_state(vehicle_id) to answer.")


if __name__ == "__main__":
    main()
