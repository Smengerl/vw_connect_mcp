"""
Tests for get_charging_status MCP Tool
=======================================

Unlike test_get_energy_status.py (which tests the underlying adapter
method directly), this file calls the actual registered MCP tool via
mcp_client, since the tool's JSON shape adds fields the adapter method
doesn't return.

What is tested:
- The response includes the resolved vehicle's `vin` and `name`, even
  when `vehicle_id` was a partial name -- so the caller can always tell
  which vehicle a response is for, regardless of how loosely it addressed
  it (see AbstractAdapter.resolve_vehicle_id's partial-name matching).
- Not-found vehicles still return a plain error, no leaked vin/name keys.
"""
import json

import pytest

from test_data import NAME_ELECTRIC, NAME_HYBRID, VIN_ELECTRIC, VIN_HYBRID, VIN_NONEXISTENT


@pytest.mark.asyncio
async def test_get_charging_status_includes_resolved_identity_for_partial_name(mcp_client):
    """A partial name like 'D7' (substring of 'ID7') must still resolve,
    and the response must say which vehicle it resolved to."""
    result = await mcp_client.call_tool("get_charging_status", {"vehicle_id": "D7"})
    data = json.loads(result.content[0].text)

    assert data["vin"] == VIN_ELECTRIC
    assert data["name"] == NAME_ELECTRIC


@pytest.mark.asyncio
async def test_get_charging_status_includes_resolved_identity_for_vin(mcp_client):
    result = await mcp_client.call_tool("get_charging_status", {"vehicle_id": VIN_HYBRID})
    data = json.loads(result.content[0].text)

    assert data["vin"] == VIN_HYBRID
    assert data["name"] == NAME_HYBRID


@pytest.mark.asyncio
async def test_get_charging_status_not_found_has_no_identity_fields(mcp_client):
    result = await mcp_client.call_tool("get_charging_status", {"vehicle_id": VIN_NONEXISTENT})
    data = json.loads(result.content[0].text)

    assert "error" in data
    assert "vin" not in data
    assert "name" not in data
