"""Read Tools Registration for MCP Server.

Provides read-only tools for vehicle data access.
All tools are idempotent and read-only (no vehicle state changes).

The Tibber Data API's confirmed 5 capabilities cover: state of charge,
target state of charge, remaining range, plug status, and charging status —
plus basic identity (VIN, brand, model, name, online state, last-seen
timestamp). See
ARCHITECTURE.md §3.1 and its data-point comparison table (§5) for the full
picture. Doors, windows, tyres,
lights, climatization, window heating, GPS position, maintenance schedule,
odometer, license plate, model year, software version, and vehicle
type/propulsion have no Tibber equivalent at all, so there are no tools
for them.
"""

from fastmcp import FastMCP
from typing import List, Optional, Annotated
from pydantic import BaseModel
import functools
import json

from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, AdapterUnavailableError, VehicleListItem,
)
from weconnect_mcp.cli import logging_config

logger = logging_config.get_logger(__name__)


def _handle_unavailable(fn):
    """Turn an AdapterUnavailableError into a clear MCP tool response,
    instead of letting FastMCP surface a bare internal exception.

    This is the one failure mode that means the *server* itself needs a
    manual step to recover (e.g. Tibber re-authorization, see
    ARCHITECTURE.md §2.4) -- not something retrying the call or trying a
    different vehicle_id can fix. Every other exception is left to
    propagate as-is.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AdapterUnavailableError as exc:
            logger.error("Adapter unavailable: %s", exc)
            return json.dumps({"error": "server_unavailable", "message": str(exc)})
    return wrapper


def register_read_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register all read-only tools with the MCP server.

    Registers 3 read tools for vehicle data access, all fully supported by
    the Tibber backend — see module docstring.

    There used to be a separate `get_vehicle_state` tool, but it called the
    exact same adapter method and returned byte-identical JSON to
    `get_vehicle_info` (no richer combined snapshot exists for this
    backend), so it was merged away rather than kept as a duplicate. There
    also used to be a separate `get_battery_status` tool, but every field it
    returned was either already present elsewhere (`battery_level_percent`
    is literally `charging.current_soc_percent` under a different name --
    see `TibberAdapter.get_energy_status()` -- and `is_charging` duplicated
    `get_charging_status`'s field of the same name) or has now been folded
    into `get_vehicle_info`/`get_charging_status` directly (`range_km`,
    `is_plugged_in`), so it was merged away too.

    Args:
        mcp: FastMCP server instance
        adapter: Vehicle data adapter
    """

    @mcp.tool(
        name="get_vehicles",
        description="List all available vehicles with VIN, name, and model. Start here to discover which vehicles you can access. license_plate is always null (Tibber does not provide it).",
        tags={"discovery", "read"},
        annotations={"title": "Get All Vehicles", "readOnlyHint": True, "idempotentHint": True}
    )
    @_handle_unavailable
    def get_vehicles() -> str:
        """Return list of all vehicles as JSON string."""
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        logger.info("Listing %d vehicles via tool", len(vehicles))
        return json.dumps([v.model_dump() for v in vehicles])

    @mcp.tool(
        name="get_vehicle_info",
        description="Get vehicle identity plus a quick energy snapshot: manufacturer, model, name, online/connection state, last-seen timestamp, electric range (km), charging flag, and plug-connected state.",
        tags={"vehicle-info", "read"},
        annotations={"title": "Get Vehicle Information", "readOnlyHint": True, "idempotentHint": True}
    )
    @_handle_unavailable
    def get_vehicle_info(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get basic vehicle information plus a quick energy snapshot."""
        logger.info("get vehicle info (tool) for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})

        result = vehicle.model_dump()
        energy_status = adapter.get_energy_status(vehicle_id)
        charging = energy_status.electric.charging if energy_status and energy_status.electric else None
        result["range_km"] = energy_status.range.electric_km if energy_status and energy_status.range else None
        result["is_charging"] = charging.is_charging if charging else None
        result["is_plugged_in"] = charging.is_plugged_in if charging else None
        return json.dumps(result)

    @mcp.tool(
        name="get_charging_status",
        description="Get charging status for electric vehicles: charging state (charging/idle), plug-connected state, target SOC, current SOC, electric range (km), and last-seen timestamp.",
        tags={"energy", "read", "charging", "bev-phev"},
        annotations={"title": "Get Charging Status", "readOnlyHint": True, "idempotentHint": True}
    )
    @_handle_unavailable
    def get_charging_status(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get charging status plus electric range."""
        logger.info("get charging status (tool) for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None or energy_status.electric is None or energy_status.electric.charging is None:
            logger.warning("Vehicle '%s' not found or doesn't support charging", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't support charging"})
        result = energy_status.electric.charging.model_dump()
        result["range_km"] = energy_status.range.electric_km if energy_status.range else None
        result["last_seen"] = energy_status.last_seen
        return json.dumps(result)
