"""Resources Registration for MCP Server.

Provides read-only resources for vehicle data access with URI-based addressing.
Resources support server-side caching and are all idempotent read operations.

The Tibber Data API's confirmed 5 capabilities cover: state of charge, target
state of charge, remaining range, plug status, and charging status — plus
basic identity (VIN, brand, model, name, online state). See
experiment/tibber-integration/TIBBER_API.md §5.2 and the README's
data-point comparison table for the full picture. There are no resources
for doors, windows, tyres, lights, climate, window heating, position,
maintenance, or vehicle type — Tibber has no equivalent data for any of them.
"""

from fastmcp import FastMCP
from typing import List, Optional, Annotated
from pydantic import BaseModel
import json

from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter, VehicleListItem
from weconnect_mcp.cli import logging_config

logger = logging_config.get_logger(__name__)


def register_resources(mcp: FastMCP, adapter: AbstractAdapter) -> None:

    @mcp.resource(
        uri="data://vehicles",
        name="res_list_vehicles",
        description="Get list of all available vehicles with basic information (VIN, name, model). license_plate is always null (Tibber does not provide it).",
        tags={"vehicle-list", "read"},
        annotations={"title": "List All Vehicles", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_list_vehicles() -> str:
        logger.info("list all vehicles")
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        return json.dumps([v.model_dump() for v in vehicles])

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/info",
        name="res_get_vehicle_info",
        description="Get basic vehicle identity: manufacturer, model, name, and online/connection state. Software version, model year, odometer, and license plate are always null (not available via Tibber).",
        tags={"vehicle-info", "read"},
        annotations={"title": "Get Vehicle Info", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_vehicle_info(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get vehicle info for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})
        return json.dumps(vehicle.model_dump() if vehicle else {})

    @mcp.resource(
        "data://vehicle/{vehicle_id}/state",
        name="res_get_vehicle_state",
        description="Get vehicle identity data (same as res_get_vehicle_info — the Tibber backend has no combined doors/windows/climate/tyre/position snapshot to add; use res_get_charging_state or res_get_range_info for energy data).",
        annotations={"title": "Get Complete Vehicle State", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_vehicle_state(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get vehicle state for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})
        return json.dumps(vehicle.model_dump() if vehicle else {})

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/charging",
        name="res_get_charging_state",
        description="Get charging status: charging state (charging/idle), plug-connected state, target SOC, and current SOC. Supported by the Tibber backend, but charging_power_kw and remaining_time_minutes are always null (Tibber does not report them).",
        annotations={"title": "Get Charging Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_charging_state(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get charging state for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None or energy_status.electric is None or energy_status.electric.charging is None:
            logger.warning("Vehicle '%s' not found or doesn't support charging", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't support charging"})
        return json.dumps(energy_status.electric.charging.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/range",
        name="res_get_range_info",
        description="Get range information: total range and electric range (km) plus battery level (%). combustion_range_km/tank_level_percent are never present (Tibber only ever reports electric vehicles).",
        annotations={"title": "Get Range Information", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_range_info(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get range info for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None:
            logger.warning("Vehicle '%s' not found or doesn't have range info", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't have range info"})

        result = {"total_range_km": energy_status.range.total_km if energy_status.range else None}

        if energy_status.electric:
            result["electric_range_km"] = energy_status.range.electric_km if energy_status.range else None
            result["battery_level_percent"] = energy_status.electric.battery_level_percent

        if energy_status.combustion:
            result["combustion_range_km"] = energy_status.range.combustion_km if energy_status.range else None
            result["tank_level_percent"] = energy_status.combustion.tank_level_percent

        return json.dumps(result)

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/battery",
        name="res_get_battery_status",
        description="Quick battery check: level (%), electric range (km), and charging status. Fully supported by the Tibber backend. Use res_get_charging_state for the plug/charging-state details.",
        annotations={"title": "Get Battery Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_battery_status(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get battery status for id=%s", vehicle_id)
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
