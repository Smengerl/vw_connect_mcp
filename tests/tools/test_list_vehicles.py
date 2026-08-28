"""
Tests for list_vehicles Tool
=============================

This test suite validates the list_vehicles() adapter method and its MCP tool registration.

What is tested:
- Returns all available vehicles
- Each vehicle contains required fields (VIN, name, model)
- Vehicle data accuracy (electric and hybrid vehicles)
- MCP server tool registration
- The get_vehicles TOOL's empty-list hint (this needs its own adapter with
  zero vehicles, so it's a tool-layer test via fastmcp.Client rather than
  a call against the shared `adapter` fixture, which always has 2)

Test data:
- Uses TestAdapter with 2 mock vehicles (ID.7 Tourer electric, T7 Multivan eHybrid hybrid)
- Expected values from tests.test_data module
"""
import json

import pytest
from fastmcp import Client

from test_data import (
    VIN_ELECTRIC,
    VIN_HYBRID,
    EXPECTED_ELECTRIC_VEHICLE,
    EXPECTED_HYBRID_VEHICLE,
)
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
from weconnect_mcp.server.mcp_server import get_server


# ==================== TESTS ====================

def test_list_vehicles_returns_all_vehicles(adapter):
    """Test that list_vehicles returns all available vehicles"""
    vehicles = adapter.list_vehicles()
    
    assert vehicles is not None
    assert len(vehicles) == 2, "Should return exactly 2 test vehicles"


def test_list_vehicles_has_required_fields(adapter):
    """Test that each vehicle has all required fields"""
    vehicles = adapter.list_vehicles()
    
    for vehicle in vehicles:
        assert vehicle.vin is not None
        assert vehicle.name is not None
        assert vehicle.model is not None


def test_list_vehicles_electric_vehicle_data(adapter):
    """Test that electric vehicle data is correct (also validates presence in list)"""
    vehicles = adapter.list_vehicles()

    electric = next((v for v in vehicles if v.vin == VIN_ELECTRIC), None)
    assert electric is not None, "Electric vehicle should be in list"
    assert electric.name == EXPECTED_ELECTRIC_VEHICLE["name"]
    assert electric.model == EXPECTED_ELECTRIC_VEHICLE["model"]


def test_list_vehicles_hybrid_vehicle_data(adapter):
    """Test that hybrid vehicle data is correct (also validates presence in list)"""
    vehicles = adapter.list_vehicles()

    hybrid = next((v for v in vehicles if v.vin == VIN_HYBRID), None)
    assert hybrid is not None, "Hybrid vehicle should be in list"
    assert hybrid.name == EXPECTED_HYBRID_VEHICLE["name"]
    assert hybrid.model == EXPECTED_HYBRID_VEHICLE["model"]


class _NoVehiclesAdapter(AbstractAdapter):
    def list_vehicles(self): return []
    def get_vehicle(self, vehicle_id, details=None): return None
    def get_energy_status(self, vehicle_id): return None
    def shutdown(self): pass


@pytest.mark.asyncio
async def test_get_vehicles_tool_includes_pairing_hint_when_empty():
    """No vehicles paired yet is a normal account state, not an error -- the
    response must say to pair one in the Tibber app instead of just
    returning a bare, unexplained empty list."""
    server = get_server(_NoVehiclesAdapter())
    async with Client(server) as client:
        result = await client.call_tool("get_vehicles", {})
        data = json.loads(result.content[0].text)

    assert data["vehicles"] == []
    assert "Tibber app" in data["hint"]
