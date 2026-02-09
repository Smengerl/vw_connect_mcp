"""Read Tools Registration for MCP Server.

Provides read-only tools for vehicle data access.
All tools are idempotent and read-only (no vehicle state changes).
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
    
    Registers 8 read tools for vehicle data access.
    
    Args:
        mcp: FastMCP server instance
        adapter: Vehicle data adapter
    """
    
    @mcp.tool(
        name="get_vehicles",
        description="List all available vehicles with VIN, name, model, and license plate. Start here to discover which vehicles you can control.",
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
        description="Get basic vehicle information including manufacturer, model, software version, year, odometer reading, and connection state",
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
        description="Get complete vehicle state snapshot including all available data: position, battery, doors, windows, climate, tyres, etc.",
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
        name="get_vehicle_doors",
        description="Get door lock status and open/closed state for all doors",
        tags={"physical", "read", "security"},
        annotations={"title": "Get Door Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def get_vehicle_doors(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get door status."""
        logger.info("get vehicle doors (tool) for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id, components=["doors"])
        if physical_status is None or physical_status.doors is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})
        return json.dumps(physical_status.doors.model_dump())
    
    @mcp.tool(
        name="get_battery_status",
        description="Quick battery check for electric/hybrid vehicles including battery level, electric range, and charging status (BEV/PHEV only)",
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
        name="get_climatization_status",
        description="Get climate control status including state (off/heating/cooling), target temperature, and estimated time remaining",
        tags={"climate", "read", "comfort"},
        annotations={"title": "Get Climate Control Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def get_climatization_status(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get climate control status."""
        logger.info("get climate status (tool) for id=%s", vehicle_id)
        climate_status = adapter.get_climate_status(vehicle_id)
        if climate_status is None or climate_status.climatization is None:
            logger.warning("Vehicle '%s' not found or doesn't support climatization", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't support climatization"})
        return json.dumps(climate_status.climatization.model_dump())
    
    @mcp.tool(
        name="get_charging_status",
        description="Get detailed charging status for electric/hybrid vehicles including charging power, remaining time, cable status, and target SOC (BEV/PHEV only)",
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
    
    @mcp.tool(
        name="get_vehicle_position",
        description="Get GPS position including latitude, longitude, and heading (0°=North, 90°=East, 180°=South, 270°=West)",
        tags={"location", "read", "gps"},
        annotations={"title": "Get Vehicle Position", "readOnlyHint": True, "idempotentHint": True}
    )
    def get_vehicle_position(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        """Get vehicle GPS position."""
        logger.info("get position (tool) for id=%s", vehicle_id)
        position = adapter.get_position(vehicle_id)
        if position is None:
            logger.warning("Vehicle '%s' not found or doesn't have position info", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't have position info"})
        return json.dumps(position.model_dump())
