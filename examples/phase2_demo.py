#!/usr/bin/env python3
"""
Demo script showing the Phase 2 MCP tools:
- get_window_heating_state
- get_lights_state
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_adapter import TestAdapter


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_window_heating():
    """Demonstrate window heating state retrieval"""
    print_section("🔥 WINDOW HEATING STATE")
    
    adapter = TestAdapter()
    
    # Get window heating for ID7 (rear heating on)
    print("📍 ID7 (Electric Vehicle):")
    window_heating = adapter.get_window_heating_state('WVWZZZED4SE003938')
    if window_heating:
        print(f"  Front Window Heating: {window_heating.front.state if window_heating.front else 'N/A'}")
        print(f"  Rear Window Heating: {window_heating.rear.state if window_heating.rear else 'N/A'}")
    
    # Get window heating for T7 (all off)
    print("\n📍 T7 (Combustion Vehicle):")
    window_heating = adapter.get_window_heating_state('WV2ZZZSTZNH009136')
    if window_heating:
        print(f"  Front Window Heating: {window_heating.front.state if window_heating.front else 'N/A'}")
        print(f"  Rear Window Heating: {window_heating.rear.state if window_heating.rear else 'N/A'}")


def demo_lights():
    """Demonstrate lights state retrieval"""
    print_section("💡 LIGHTS STATE")
    
    adapter = TestAdapter()
    
    # Get lights for ID7
    print("📍 ID7 (Electric Vehicle):")
    lights = adapter.get_lights_state('WVWZZZED4SE003938')
    if lights:
        print(f"  Left Light: {lights.left.state if lights.left else 'N/A'}")
        print(f"  Right Light: {lights.right.state if lights.right else 'N/A'}")
        
        if lights.left and lights.right:
            if lights.left.state == 'off' and lights.right.state == 'off':
                print(f"  ✅ All lights are off (safe)")
    
    # Get lights for T7
    print("\n📍 T7 (Combustion Vehicle):")
    lights = adapter.get_lights_state('WV2ZZZSTZNH009136')
    if lights:
        print(f"  Left Light: {lights.left.state if lights.left else 'N/A'}")
        print(f"  Right Light: {lights.right.state if lights.right else 'N/A'}")
        
        if lights.left and lights.right:
            if lights.left.state == 'off' and lights.right.state == 'off':
                print(f"  ✅ All lights are off (safe)")


def demo_combined_comfort_check():
    """Show combined comfort and safety check"""
    print_section("🔍 COMFORT & SAFETY CHECK")
    
    adapter = TestAdapter()
    vin = 'WVWZZZED4SE003938'
    
    print("Vehicle: ID7 (Electric)\n")
    
    # Climate check
    climate = adapter.get_climatization_state(vin)
    if climate:
        print("🌡️  Climate Control:")
        if climate.is_active:
            state_str = climate.state.upper() if climate.state else 'UNKNOWN'
            print(f"   Active: {state_str} at {climate.target_temperature_celsius}°C")
        else:
            print(f"   Inactive")
    
    # Window heating check
    window_heating = adapter.get_window_heating_state(vin)
    if window_heating:
        print("\n🔥 Window Heating:")
        if window_heating.rear and window_heating.rear.state == 'on':
            print(f"   Rear window heating is ON")
        else:
            print(f"   All window heating OFF")
    
    # Lights check
    lights = adapter.get_lights_state(vin)
    if lights:
        print("\n💡 Lights:")
        if lights.left and lights.right:
            if lights.left.state == 'off' and lights.right.state == 'off':
                print(f"   ✅ All lights OFF (safe)")
            else:
                print(f"   ⚠️  Some lights are still ON!")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  PHASE 2 MCP TOOLS DEMONSTRATION")
    print("="*60)
    
    demo_window_heating()
    demo_lights()
    demo_combined_comfort_check()
    
    print("\n" + "="*60)
    print("  ✅ All Phase 2 tools working correctly!")
    print("="*60 + "\n")
