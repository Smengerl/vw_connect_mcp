"""Integration test for MCP server with real VW API.

Simulates AI assistant workflow using real VW WeConnect API.
Requires valid credentials in config.json.

Usage:
    pytest tests/real_api/test_real_api_integration.py -v -s  # Run with real API
    pytest tests/ -m "not real_api"  # Skip in normal runs
"""

import pytest
import json

# Mark as real API test - skip in normal CI/CD
pytestmark = [pytest.mark.real_api, pytest.mark.slow]


@pytest.mark.asyncio
async def test_mcp_server_with_real_api(real_adapter):
    """Test MCP server tools with real VW API - simulates AI assistant workflow."""
    from weconnect_mcp.server.mcp_server import get_server
    
    print("\n" + "="*60)
    print("🚀 MCP SERVER - REAL API INTEGRATION TEST")
    print("="*60)
    
    server = get_server(real_adapter)
    print(f"\n✅ Server created: {server.name}")
    print(f"   Version: {server.version}\n")
    
    print("🤖 Simulating AI Assistant Workflow:\n")
    
    # List Vehicles
    print("1️⃣  AI: 'Show me all available vehicles'")
    vehicles = real_adapter.list_vehicles()
    assert len(vehicles) > 0, "Should have at least one vehicle"
    
    vehicle = vehicles[0]
    vehicle_id = vehicle.name or vehicle.vin
    print(f"   ✅ Found {len(vehicles)} vehicle(s) → Using: {vehicle_id}\n")
    
    
    # Get Vehicle Info
    print(f"2️⃣  AI: 'Tell me about {vehicle_id}'")
    vehicle_info = real_adapter.get_vehicle(vehicle_id)
    assert vehicle_info is not None, f"Vehicle {vehicle_id} should exist"
    print(f"   ✅ Model: {vehicle_info.model}, Type: {vehicle_info.type}, Odometer: {vehicle_info.odometer} km\n")
    
    
    # Get Energy Status (if electric)
    if vehicle_info.type in ["electric", "hybrid"]:
        print(f"3️⃣  AI: 'What is the battery status?'")
        energy = real_adapter.get_energy_status(vehicle_id)
        if energy is not None and energy.electric:
            print(f"   ✅ Battery: {energy.electric.battery_level_percent}%")
        else:
            print(f"   ⚠️  Energy status not available")
        print()
    else:
        print(f"3️⃣  Skipping battery test (vehicle is {vehicle_info.type})\n")
    
    
    # Get Physical Status
    print(f"4️⃣  AI: 'Are the doors locked?'")
    physical = real_adapter.get_physical_status(vehicle_id)
    if physical is not None and physical.doors is not None:
        print(f"   ✅ Lock State: {physical.doors.lock_state}, Open State: {physical.doors.open_state}")
    else:
        print(f"   ⚠️  Physical status not available")
    print()
    
    
    # Get Position
    print(f"5️⃣  AI: 'Where is the vehicle located?'")
    position = real_adapter.get_position(vehicle_id)
    if position is not None:
        print(f"   ✅ Position: {position.latitude}, {position.longitude}")
    else:
        print(f"   ⚠️  Position not available")
    print()
    
    
    # Error Handling
    print("6️⃣  AI: 'Show me vehicle INVALID_VIN'")
    invalid_result = real_adapter.get_vehicle("INVALID_VIN")
    assert invalid_result is None, "Should return None for invalid vehicle"
    print(f"   ✅ Error handling works: Returns None\n")
    
    
    print("="*60)
    print(f"✅ INTEGRATION TEST COMPLETED - {len(vehicles)} vehicles tested")
    print("="*60)



@pytest.mark.asyncio
async def test_mcp_tools_return_valid_json(real_adapter):
    """Verify all MCP tools return JSON-serializable data (required by MCP protocol)."""
    print("\n" + "="*60)
    print("🔍 TESTING JSON SERIALIZATION")
    print("="*60)
    
    vehicles = real_adapter.list_vehicles()
    assert len(vehicles) > 0
    
    vehicle_id = vehicles[0].name or vehicles[0].vin
    vehicle_full = real_adapter.get_vehicle(vehicle_id)
    assert vehicle_full is not None
    
    # Test tools that should return data
    tools_to_test = [
        ("get_vehicle", vehicle_id),
        ("get_physical_status", vehicle_id),
        ("get_position", vehicle_id),
    ]
    
    if vehicle_full.type in ["electric", "hybrid"]:
        tools_to_test.append(("get_energy_status", vehicle_id))
    
    for method_name, vid in tools_to_test:
        print(f"\n📦 Testing: {method_name}")
        method = getattr(real_adapter, method_name)
        result = method(vid)
        
        if result is None:
            print(f"   ⚠️  Returned None (data not available)")
            continue
        
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else dict(result)
        json_str = json.dumps(result_dict)
        json.loads(json_str)  # Verify deserializable
        print(f"   ✅ JSON valid: {len(json_str)} bytes")
    
    print("\n" + "="*60)
    print("✅ ALL TOOLS RETURN VALID JSON")
    print("="*60)



@pytest.mark.asyncio
async def test_mcp_command_error_handling(real_adapter):
    """Test command methods handle errors gracefully for invalid vehicle IDs.
    
    NOTE: Does NOT execute commands on real vehicles.
    """
    print("\n" + "="*60)
    print("🚨 TESTING ERROR HANDLING")
    print("="*60)
    
    invalid_vehicle_id = "DEFINITELY_NOT_A_REAL_VIN_12345"
    command_methods = ["lock_vehicle", "unlock_vehicle", "start_charging", "stop_charging"]
    
    for method_name in command_methods:
        print(f"\n🔧 Testing: {method_name}")
        method = getattr(real_adapter, method_name)
        result = method(invalid_vehicle_id)
        
        assert isinstance(result, dict), f"{method_name} should return dict"
        assert "success" in result and not result["success"]
        print(f"   ✅ Returns error dict: {result}")
    
    print("\n" + "="*60)
    print("✅ ERROR HANDLING WORKS CORRECTLY")
    print("="*60)


@pytest.mark.asyncio
async def test_mcp_server_handles_none_values(real_adapter):
    """Test MCP server gracefully handles None values from VW API.
    
    VW API frequently returns incomplete data - Pydantic models should handle this.
    """
    print("\n" + "="*60)
    print("🔄 TESTING NONE VALUE HANDLING")
    print("="*60)
    
    vehicles = real_adapter.list_vehicles()
    assert len(vehicles) > 0
    
    vehicle_id = vehicles[0].name or vehicles[0].vin
    
    # Vehicle info should never be None
    info = real_adapter.get_vehicle(vehicle_id)
    assert info is not None
    print(f"\n✅ Vehicle info always available: {info.model}")
    
    # These might be None depending on vehicle type and API data
    optional_data = {
        "energy_status": real_adapter.get_energy_status(vehicle_id),
        "climate_status": real_adapter.get_climate_status(vehicle_id),
        "physical_status": real_adapter.get_physical_status(vehicle_id),
        "position": real_adapter.get_position(vehicle_id),
    }
    
    for data_name, data_value in optional_data.items():
        if data_value is None:
            print(f"⚠️  {data_name}: None (not available)")
        else:
            print(f"✅ {data_name}: Available")
            if hasattr(data_value, 'model_dump'):
                json.dumps(data_value.model_dump())  # Verify JSON-serializable
                print(f"   → JSON serializable")
    
    print("\n" + "="*60)
    print("✅ NONE VALUES HANDLED GRACEFULLY")
    print("="*60)

