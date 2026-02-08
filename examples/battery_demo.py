#!/usr/bin/env python3
"""
Demo script showing how to use the get_battery_status tool.

This demonstrates retrieving battery level, range, and charging status
for electric and hybrid vehicles.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_adapter import TestAdapter


def format_charging_status(battery):
    """Format charging status in a human-readable way."""
    if battery.is_charging:
        status = f"⚡ Charging at {battery.charging_power_kw} kW"
        if battery.estimated_charge_time_minutes:
            hours = battery.estimated_charge_time_minutes // 60
            minutes = battery.estimated_charge_time_minutes % 60
            if hours > 0:
                status += f" (Est. {hours}h {minutes}m remaining)"
            else:
                status += f" (Est. {minutes}m remaining)"
        return status
    else:
        return "🔌 Not charging"


def format_battery_level(percent):
    """Format battery level with emoji indicator."""
    if percent >= 80:
        emoji = "🟢"
    elif percent >= 50:
        emoji = "🟡"
    elif percent >= 20:
        emoji = "🟠"
    else:
        emoji = "🔴"
    
    return f"{emoji} {percent}%"


def format_range(km):
    """Format range with visual indicator."""
    miles = km * 0.621371
    
    if km >= 300:
        indicator = "✅"
    elif km >= 150:
        indicator = "⚠️"
    else:
        indicator = "🔋"
    
    return f"{indicator} {km:.0f} km ({miles:.0f} mi)"


def main():
    print("=" * 70)
    print("Battery Status Demo")
    print("=" * 70)
    print()
    
    # Create adapter with mock data
    adapter = TestAdapter()
    
    # List all vehicles
    vehicles = adapter.list_vehicles()
    print(f"Found {len(vehicles)} vehicles:\n")
    
    for vehicle in vehicles:
        print(f"🚗 {vehicle.name} ({vehicle.model})")
        print(f"   VIN: {vehicle.vin}")
        print("-" * 70)
        
        # Get battery status
        battery = adapter.get_battery_status(vehicle.vin)
        
        if battery:
            print(f"   Battery Level: {format_battery_level(battery.battery_level_percent)}")
            print(f"   Electric Range: {format_range(battery.range_km)}")
            print(f"   Status: {format_charging_status(battery)}")
        else:
            print(f"   ❌ No battery (combustion vehicle)")
        
        print()
    
    print("=" * 70)
    print("Demo: Battery Status Use Cases")
    print("=" * 70)
    print()
    
    # Example 1: Quick range check
    print("Use Case 1: Quick Range Check")
    print("-" * 70)
    id7_battery = adapter.get_battery_status("WVWZZZED4SE003938")
    if id7_battery:
        print(f"Question: 'Can I drive to the airport (45 km)?'")
        if id7_battery.range_km and id7_battery.range_km >= 45:
            print(f"Answer: ✅ Yes! You have {id7_battery.range_km:.0f} km range.")
        else:
            print(f"Answer: ❌ No, only {id7_battery.range_km:.0f} km range.")
    print()
    
    # Example 2: Charging time estimate
    print("Use Case 2: Charging Time Estimate")
    print("-" * 70)
    if id7_battery and id7_battery.is_charging:
        print(f"Question: 'When will my car be fully charged?'")
        if id7_battery.estimated_charge_time_minutes:
            from datetime import datetime, timedelta
            now = datetime.now()
            finish_time = now + timedelta(minutes=id7_battery.estimated_charge_time_minutes)
            print(f"Answer: Around {finish_time.strftime('%H:%M')} ")
            print(f"        ({id7_battery.estimated_charge_time_minutes} minutes from now)")
        else:
            print(f"Answer: Charge time not available")
    else:
        print(f"Vehicle is not currently charging")
    print()
    
    # Example 3: Battery health monitoring
    print("Use Case 3: Battery Level Monitoring")
    print("-" * 70)
    for vehicle in vehicles:
        battery = adapter.get_battery_status(vehicle.vin)
        if battery and battery.battery_level_percent is not None:
            status_emoji = "✅" if battery.battery_level_percent >= 20 else "⚠️"
            print(f"{status_emoji} {vehicle.name}: {battery.battery_level_percent}% ")
            
            if battery.battery_level_percent < 20:
                print(f"   ⚠️  Low battery! Consider charging soon.")
            elif battery.battery_level_percent >= 80:
                print(f"   ✅ Battery well charged.")
        else:
            print(f"❌ {vehicle.name}: Not an electric vehicle")
    print()
    
    # Example 4: Range anxiety checker
    print("Use Case 4: Range Anxiety Checker")
    print("-" * 70)
    print("Planning a 100 km trip...")
    for vehicle in vehicles:
        battery = adapter.get_battery_status(vehicle.vin)
        if battery and battery.range_km:
            trip_distance = 100
            margin = battery.range_km - trip_distance
            
            if margin >= 50:
                status = "✅ Comfortable"
            elif margin >= 0:
                status = "⚠️  Tight"
            else:
                status = "❌ Insufficient"
            
            print(f"{vehicle.name}: {status} ")
            print(f"  Range: {battery.range_km:.0f} km | Needed: {trip_distance} km | Margin: {margin:.0f} km")
    print()
    
    # Example 5: Compare battery_status vs detailed tools
    print("Use Case 5: Tool Comparison")
    print("-" * 70)
    print("get_battery_status() - Quick Overview:")
    if id7_battery:
        print(f"  • Battery: {id7_battery.battery_level_percent}%")
        print(f"  • Range: {id7_battery.range_km} km")
        print(f"  • Charging: {id7_battery.is_charging}")
    print()
    
    print("get_range_info() - Complete Range Details:")
    range_info = adapter.get_range_info("WVWZZZED4SE003938")
    if range_info:
        print(f"  • Total Range: {range_info.total_range_km} km")
        if range_info.electric_drive:
            print(f"  • Electric: {range_info.electric_drive.range_km} km @ {range_info.electric_drive.battery_level_percent}%")
        if range_info.combustion_drive:
            print(f"  • Fuel: {range_info.combustion_drive.range_km} km @ {range_info.combustion_drive.tank_level_percent}%")
    print()
    
    print("get_charging_state() - Detailed Charging:")
    charging = adapter.get_charging_state("WVWZZZED4SE003938")
    if charging:
        print(f"  • State: {charging.charging_state}")
        print(f"  • Power: {charging.charging_power_kw} kW")
        print(f"  • Current SOC: {charging.current_soc_percent}%")
        print(f"  • Target SOC: {charging.target_soc_percent}%")
        print(f"  • Time Remaining: {charging.remaining_time_minutes} min")
    print()
    
    print("=" * 70)
    print("Recommendation:")
    print("  • Use get_battery_status() for quick checks")
    print("  • Use get_range_info() for hybrid vehicles or trip planning")
    print("  • Use get_charging_state() for detailed charging management")
    print("=" * 70)


if __name__ == "__main__":
    main()
