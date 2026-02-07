#!/usr/bin/env python3
"""
Test script to verify the MCP server tools work correctly.
This simulates how an AI would interact with the server.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from weconnect_mcp.server.mcp_server import get_server
from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, DoorsModel, WindowsModel, TyresModel,
    PositionModel, BatteryModel, DoorModel, WindowModel, TyreModel
)
from typing import Optional, List


class MockAdapter(AbstractAdapter):
    """Mock adapter for testing without real VW connection."""
    
    def __init__(self):
        self.vehicles = {
            "WVWZZZ1KZBW123456": VehicleModel(
                vin="WVWZZZ1KZBW123456",
                model="ID.3",
                name="Mein ID.3",
                odometer=15234.5,
                manufacturer="Volkswagen",
                state="ready",
                type="electric",
                position=PositionModel(
                    latitude=52.520008,
                    longitude=13.404954,
                    heading=45.0
                ),
                battery=BatteryModel(
                    soc=78.5,
                    range_km=245.0,
                    charging=False,
                    plugged_in=True,
                    charging_power=0.0
                ),
                doors=DoorsModel(
                    lock_state=True,
                    open_state=False,
                    front_left=DoorModel(locked=True, open=False),
                    front_right=DoorModel(locked=True, open=False),
                    rear_left=DoorModel(locked=True, open=False),
                    rear_right=DoorModel(locked=True, open=False),
                    trunk=DoorModel(locked=True, open=False),
                    bonnet=DoorModel(locked=True, open=False)
                ),
                windows=WindowsModel(
                    front_left=WindowModel(open=False),
                    front_right=WindowModel(open=False),
                    rear_left=WindowModel(open=False),
                    rear_right=WindowModel(open=False)
                ),
                tyres=TyresModel(
                    front_left=TyreModel(pressure=2.4, temperature=22.0),
                    front_right=TyreModel(pressure=2.4, temperature=22.0),
                    rear_left=TyreModel(pressure=2.2, temperature=21.0),
                    rear_right=TyreModel(pressure=2.2, temperature=21.0)
                )
            )
        }
    
    def shutdown(self) -> None:
        pass
    
    def list_vehicles(self) -> List[str]:
        return list(self.vehicles.keys())
    
    def get_vehicle(self, vehicle_id: str) -> Optional[VehicleModel]:
        return self.vehicles.get(vehicle_id)
    
    def get_doors_state(self, vehicle_id: str) -> Optional[DoorsModel]:
        vehicle = self.vehicles.get(vehicle_id)
        return vehicle.doors if vehicle else None
    
    def get_windows_state(self, vehicle_id: str) -> Optional[WindowsModel]:
        vehicle = self.vehicles.get(vehicle_id)
        return vehicle.windows if vehicle else None
    
    def get_tyres_state(self, vehicle_id: str) -> Optional[TyresModel]:
        vehicle = self.vehicles.get(vehicle_id)
        return vehicle.tyres if vehicle else None


def test_server():
    """Test the MCP server with mock data."""
    print("🚀 Starting MCP Server Test\n")
    
    # Create server with mock adapter
    adapter = MockAdapter()
    server = get_server(adapter)
    
    print(f"✅ Server created: {server.name}")
    print(f"   Version: {server.version}")
    print(f"   Instructions: {server.instructions.strip()}\n")
    
    # Check registered tools
    tools = server.list_tools()
    print(f"📋 Registered Tools ({len(tools)}):")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description}")
    print()
    
    # Check registered resources
    resources = server.list_resources()
    print(f"📦 Registered Resources ({len(resources)}):")
    for resource in resources:
        print(f"   - {resource.uri}: {resource.name}")
    print()
    
    # Simulate AI calling tools
    print("🤖 Simulating AI Interactions:\n")
    
    # Test 1: List vehicles
    print("1️⃣  AI calls: list_vehicles()")
    try:
        result = server.call_tool("list_vehicles", {})
        print(f"   Result: {result}")
        if result:
            vehicle_id = result[0] if isinstance(result, list) else None
            print(f"   ✅ Found vehicle: {vehicle_id}\n")
        else:
            print("   ❌ No vehicles found\n")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return
    
    # Test 2: Get vehicle state
    print(f"2️⃣  AI calls: get_vehicle_state(vehicle_id='{vehicle_id}')")
    try:
        result = server.call_tool("get_vehicle_state", {"vehicle_id": vehicle_id})
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"   Model: {result.get('model')}")
        print(f"   Battery SOC: {result.get('battery', {}).get('soc')}%")
        print(f"   Range: {result.get('battery', {}).get('range_km')} km")
        print(f"   ✅ State retrieved successfully\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Test 3: Get doors
    print(f"3️⃣  AI calls: get_vehicle_doors(vehicle_id='{vehicle_id}')")
    try:
        result = server.call_tool("get_vehicle_doors", {"vehicle_id": vehicle_id})
        print(f"   Lock state: {result.get('lock_state')}")
        print(f"   Open state: {result.get('open_state')}")
        print(f"   ✅ Doors retrieved successfully\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Test 4: Get windows
    print(f"4️⃣  AI calls: get_vehicle_windows(vehicle_id='{vehicle_id}')")
    try:
        result = server.call_tool("get_vehicle_windows", {"vehicle_id": vehicle_id})
        print(f"   Result: {result}")
        print(f"   ✅ Windows retrieved successfully\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Test 5: Get tyres
    print(f"5️⃣  AI calls: get_vehicle_tyres(vehicle_id='{vehicle_id}')")
    try:
        result = server.call_tool("get_vehicle_tyres", {"vehicle_id": vehicle_id})
        print(f"   Front left: {result.get('front_left', {}).get('pressure')} bar")
        print(f"   ✅ Tyres retrieved successfully\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Test 6: Error handling
    print("6️⃣  AI calls: get_vehicle_state(vehicle_id='INVALID')")
    try:
        result = server.call_tool("get_vehicle_state", {"vehicle_id": "INVALID"})
        print(f"   Result: {result}")
        if result.get('error'):
            print(f"   ✅ Error handling works correctly\n")
        else:
            print(f"   ⚠️  Expected error but got: {result}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    test_server()
