"""Read Tools Registration for MCP Server.

Provides read-only tools for vehicle data access.
All tools are idempotent and read-only (no vehicle state changes).

The Tibber Data API's confirmed 5 capabilities cover: state of charge,
target state of charge, remaining range, plug status, and charging status —
plus basic identity (VIN, brand, model, name, online state). See
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
import json

from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter, VehicleListItem
from weconnect_mcp.cli import logging_config

logger = logging_config.get_logger(__name__)


def register_read_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register all read-only tools with the MCP server.

    Registers 5 read tools for vehicle data access, all fully supported by
    the Tibber backend — see module docstring.

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
    def get_vehicles() -> str:
        """Return list of all vehicles as JSON string."""
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        logger.info("Listing %d vehicles via tool", len(vehicles))
        return json.dumps([v.model_dump() for v in vehicles])

    @mcp.tool(
        name="get_vehicle_info",
        description="Get basic vehicle identity: manufacturer, model, name, and online/connection state. Software version, model year, odometer, and license plate are always null (not available via Tibber).",
        tags={"vehicle-info", "read"},
        annotations={"title": "Get Vehicle Information", "readOnlyHint": True, "idempotentHint": True}
    )
    def get_vehicle_info(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get basic vehicle information."""
        logger.info("get vehicle info (tool) for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})
        return json.dumps(vehicle.model_dump() if vehicle else {})

    @mcp.tool(
        name="get_vehicle_state",
        description="Get vehicle identity plus energy state (this is the same identity data as get_vehicle_info — with the Tibber backend there is no combined doors/windows/climate/tyres snapshot to add; use get_energy_status/get_charging_status/get_battery_status for the rest).",
        tags={"vehicle-info", "read", "comprehensive"},
        annotations={"title": "Get Complete Vehicle State", "readOnlyHint": True, "idempotentHint": True}
    )
    def get_vehicle_state(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get complete vehicle state."""
        logger.info("get vehicle state (tool) for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})
        return json.dumps(vehicle.model_dump() if vehicle else {})

    @mcp.tool(
        name="get_battery_status",
        description="Quick battery check for electric vehicles: battery level (%), electric range (km), and whether it's currently charging. Fully supported by the Tibber backend.",
        tags={"energy", "read", "battery", "bev-phev"},
        annotations={"title": "Get Battery Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def get_battery_status(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get battery status."""
        logger.info("get battery status (tool) for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None or energy_status.electric is None:
            logger.warning("Vehicle '%s' not found or doesn't have a battery", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't have a battery"})

        result = {
            "battery_level_percent": energy_status.electric.battery_level_percent,
            "range_km": energy_status.range.electric_km if energy_status.range else None,
            "is_charging": energy_status.electric.charging.is_charging if energy_status.electric.charging else False
        }

        if energy_status.electric.charging and energy_status.electric.charging.is_charging:
            result["charging_power_kw"] = energy_status.electric.charging.charging_power_kw
            result["estimated_charge_time_minutes"] = energy_status.electric.charging.remaining_time_minutes

        return json.dumps(result)

    @mcp.tool(
        name="get_charging_status",
        description="Get charging status for electric vehicles: charging state (charging/idle), plug-connected state, target SOC, and current SOC. Supported by the Tibber backend, but charging_power_kw and remaining_time_minutes are always null (Tibber does not report them).",
        tags={"energy", "read", "charging", "bev-phev"},
        annotations={"title": "Get Charging Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def get_charging_status(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get charging status."""
        logger.info("get charging status (tool) for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None or energy_status.electric is None or energy_status.electric.charging is None:
            logger.warning("Vehicle '%s' not found or doesn't support charging", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't support charging"})
        return json.dumps(energy_status.electric.charging.model_dump())
