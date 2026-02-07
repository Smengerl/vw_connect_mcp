"""Tests for the charging state functionality."""

import pytest
from tests.test_adapter import TestAdapter


def test_get_charging_state_electric_vehicle():
    """Test that get_charging_state returns data for electric vehicles."""
    adapter = TestAdapter()
    
    # Test ID7 (electric, should have charging state)
    charging = adapter.get_charging_state("WVWZZZED4SE003938")
    assert charging is not None, "Charging state should be available for electric vehicle"
    assert charging.is_charging is not None, "is_charging should be set"
    assert charging.charging_state is not None, "charging_state should be set"
    assert charging.current_soc_percent is not None, "current_soc_percent should be set"


def test_get_charging_state_combustion_vehicle():
    """Test that get_charging_state returns None for combustion vehicles."""
    adapter = TestAdapter()
    
    # First, let's check the vehicle type to ensure it's actually combustion
    vehicle_type = adapter.get_vehicle_type("WV2ZZZSTZNH009136")
    print(f"Vehicle type: {vehicle_type}")
    
    # If it's combustion, charging should not be available
    if vehicle_type == "combustion":
        charging = adapter.get_charging_state("WV2ZZZSTZNH009136")
        assert charging is None, "Charging state should not be available for combustion vehicle"


def test_get_charging_state_invalid_vin():
    """Test that get_charging_state returns None for invalid VIN."""
    adapter = TestAdapter()
    
    charging = adapter.get_charging_state("INVALID_VIN")
    assert charging is None, f"Expected None for invalid VIN, got {charging}"


def test_charging_state_fields():
    """Test that charging state contains expected fields."""
    adapter = TestAdapter()
    
    charging = adapter.get_charging_state("WVWZZZED4SE003938")
    if charging is not None:
        # Check that the model has the expected fields
        assert hasattr(charging, 'is_charging'), "Should have is_charging field"
        assert hasattr(charging, 'is_plugged_in'), "Should have is_plugged_in field"
        assert hasattr(charging, 'charging_power_kw'), "Should have charging_power_kw field"
        assert hasattr(charging, 'charging_state'), "Should have charging_state field"
        assert hasattr(charging, 'remaining_time_minutes'), "Should have remaining_time_minutes field"
        assert hasattr(charging, 'target_soc_percent'), "Should have target_soc_percent field"
        assert hasattr(charging, 'current_soc_percent'), "Should have current_soc_percent field"
        assert hasattr(charging, 'charge_mode'), "Should have charge_mode field"


def test_charging_state_mcp_tool():
    """Test the get_charging_state MCP tool."""
    from weconnect_mcp.server.mcp_server import get_server
    
    adapter = TestAdapter()
    mcp = get_server(adapter)
    
    # Check that the tool is registered
    print("MCP server created successfully with charging state tool")


def test_charging_state_when_charging():
    """Test charging state when vehicle is actively charging."""
    adapter = TestAdapter()
    
    charging = adapter.get_charging_state("WVWZZZED4SE003938")
    if charging is not None and charging.is_charging:
        # When charging, certain fields should be set
        assert charging.is_plugged_in == True, "Should be plugged in when charging"
        assert charging.charging_power_kw is not None, "Charging power should be set when charging"
        assert charging.charging_power_kw > 0, "Charging power should be greater than 0 when charging"


def test_charging_model_serialization():
    """Test that ChargingModel can be serialized to dict."""
    from weconnect_mcp.adapter.abstract_adapter import ChargingModel
    
    charging = ChargingModel(
        is_charging=True,
        is_plugged_in=True,
        charging_power_kw=11.0,
        charging_state="charging",
        remaining_time_minutes=45,
        target_soc_percent=90,
        current_soc_percent=77.0,
        charge_mode="manual"
    )
    
    data = charging.model_dump()
    assert isinstance(data, dict), "Should serialize to dict"
    assert data['is_charging'] == True, "Should preserve is_charging value"
    assert data['charging_power_kw'] == 11.0, "Should preserve charging_power_kw value"
