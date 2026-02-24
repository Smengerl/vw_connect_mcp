"""Resources Registration for MCP Server.

Provides read-only resources for vehicle data access with URI-based addressing.
Resources support server-side caching and are all idempotent read operations.
"""

from fastmcp import FastMCP
from typing import List, Optional, Annotated
from pydantic import BaseModel
import json

from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleListItem, VehicleDetailLevel
)
from weconnect_mcp.cli import logging_config

logger = logging_config.get_logger(__name__)


def register_resources(mcp: FastMCP, adapter: AbstractAdapter) -> None:

    @mcp.resource(
        uri="data://vehicles",
        name="res_list_vehicles",
        description="Get list of all available vehicles with basic information (VIN, name, model, license plate)",
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
        description="Get basic vehicle information including manufacturer, model, software version, year, odometer reading, and connection state",
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
        description="Get complete vehicle state including position, battery, doors, windows, climate control, and tyre information",
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
        uri="data://vehicle/{vehicle_id}/doors",
        name="res_get_vehicle_doors",
        description="Get door lock status and open/closed state for all doors",
        tags={"physical", "read", "security"},
        annotations={"title": "Get Door Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_vehicle_doors(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get vehicle doors for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id, components=["doors"])
        if physical_status is None or physical_status.doors is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})
        return json.dumps(physical_status.doors.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/windows",
        name="res_get_vehicle_windows",
        description="Get open/closed status for all windows",
        annotations={"title": "Get Window Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_vehicle_windows(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get vehicle windows for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id, components=["windows"])
        if physical_status is None or physical_status.windows is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})
        return json.dumps(physical_status.windows.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/tyres",
        name="res_get_vehicle_tyres",
        description="Get tyre pressure and temperature for all tyres",
        annotations={"title": "Get Tyre Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_vehicle_tyres(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get vehicle tyres for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id, components=["tyres"])
        if physical_status is None or physical_status.tyres is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found"})
        return json.dumps(physical_status.tyres.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/type",
        name="res_get_vehicle_type",
        description="Get vehicle propulsion type: electric (BEV), combustion engine, or plug-in hybrid (PHEV)",
        annotations={"title": "Get Vehicle Type", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_vehicle_type(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get vehicle type for id=%s", vehicle_id)
        vehicle = adapter.get_vehicle(vehicle_id, details=VehicleDetailLevel.BASIC)
        if vehicle is None or vehicle.type is None:
            logger.warning("Vehicle '%s' not found or type not available", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or type not available"})
        return json.dumps({"vehicle_id": vehicle_id, "type": vehicle.type})

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/charging",
        name="res_get_charging_state",
        description="Get detailed charging status for electric/hybrid vehicles including charging power, remaining time, battery level, and charging state (BEV/PHEV only)",
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
        uri="data://vehicle/{vehicle_id}/climate",
        name="res_get_climatization_state",
        description="Get climate control status including state, target temperature, and window/seat heating settings",
        annotations={"title": "Get Climate Control Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_climatization_state(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get climatization state for id=%s", vehicle_id)
        climate_status = adapter.get_climate_status(vehicle_id)
        if climate_status is None or climate_status.climatization is None:
            logger.warning("Vehicle '%s' not found or doesn't support climatization", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't support climatization"})
        return json.dumps(climate_status.climatization.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/maintenance",
        name="res_get_maintenance_info",
        description="Get service schedules including inspection and oil service due dates and remaining distances",
        annotations={"title": "Get Maintenance Information", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_maintenance_info(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get maintenance info for id=%s", vehicle_id)
        maintenance_info = adapter.get_maintenance_info(vehicle_id)
        if maintenance_info is None:
            logger.warning("Vehicle '%s' not found or doesn't have maintenance info", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't have maintenance info"})
        return json.dumps(maintenance_info.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/range",
        name="res_get_range_info",
        description="Get range information including total range, electric range (BEV/PHEV), combustion range (PHEV/ICE), and battery/fuel tank levels",
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
        uri="data://vehicle/{vehicle_id}/window-heating",
        name="res_get_window_heating_state",
        description="Get window heating/defrosting status for front and rear windows",
        annotations={"title": "Get Window Heating State", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_window_heating_state(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get window heating state for id=%s", vehicle_id)
        climate_status = adapter.get_climate_status(vehicle_id)
        if climate_status is None or climate_status.window_heating is None:
            logger.warning("Vehicle '%s' not found or doesn't have window heating info", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't have window heating info"})
        return json.dumps(climate_status.window_heating.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/lights",
        name="res_get_lights_state",
        description="Get status of vehicle lights (left/right on/off)",
        annotations={"title": "Get Lights Status", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_lights_state(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get lights state for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id)
        if physical_status is None or physical_status.lights is None:
            logger.warning("Vehicle '%s' not found or doesn't have lights info", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't have lights info"})
        return json.dumps(physical_status.lights.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/position",
        name="res_get_position",
        description="Get vehicle GPS position including latitude, longitude, and heading (0=North, 90=East, 180=South, 270=West)",
        annotations={"title": "Get GPS Position", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_position(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> str:
        logger.info("get position for id=%s", vehicle_id)
        position = adapter.get_position(vehicle_id)
        if position is None:
            logger.warning("Vehicle '%s' not found or doesn't have position info", vehicle_id)
            return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't have position info"})
        return json.dumps(position.model_dump())

    @mcp.resource(
        uri="data://vehicle/{vehicle_id}/battery",
        name="res_get_battery_status",
        description="Quick battery check including level, electric range, and charging status (BEV/PHEV only). Use get_charging_state for detailed charging information",
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
