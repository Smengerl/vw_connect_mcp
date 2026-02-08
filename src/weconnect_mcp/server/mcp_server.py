from fastmcp import FastMCP
from typing import List, Dict, Any, Optional, Annotated
from pathlib import Path
from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleListItem, VehicleDetailLevel, 
    ChargingModel, ClimatizationModel, MaintenanceModel, RangeModel, 
    WindowHeatingsModel, LightsModel
)
from carconnectivity.vehicle import GenericVehicle
from pydantic import BaseModel
import json

from weconnect_mcp.cli import logging_config
logger = logging_config.get_logger(__name__)

def _register_read_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register read-only tools for vehicle data access."""
    
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

def _register_command_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register command tools for vehicle control."""
    
    @mcp.tool(
        name="lock_vehicle",
        description="Lock all vehicle doors remotely",
        tags={"command", "security", "write"},
        annotations={"title": "Lock Vehicle", "readOnlyHint": False}
    )
    def lock_vehicle(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> Dict[str, Any]:
        logger.info("lock vehicle for id=%s", vehicle_id)
        return adapter.lock_vehicle(vehicle_id)

    @mcp.tool(
        name="unlock_vehicle",
        description="Unlock all vehicle doors remotely",
        tags={"command", "security", "write"},
        annotations={"title": "Unlock Vehicle", "readOnlyHint": False}
    )
    def unlock_vehicle(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> Dict[str, Any]:
        logger.info("unlock vehicle for id=%s", vehicle_id)
        return adapter.unlock_vehicle(vehicle_id)

    @mcp.tool(
        name="start_climatization",
        description="Start vehicle climate control (heating/cooling). Optional target temperature in Celsius.",
        tags={"command", "climate", "comfort", "write"},
        annotations={"title": "Start Climate Control", "readOnlyHint": False}
    )
    def start_climatization(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"],
        target_temp_celsius: Annotated[Optional[float], "Target temperature in Celsius (if supported by vehicle)"] = None
    ) -> Dict[str, Any]:
        logger.info("start climatization for id=%s, temp=%s", vehicle_id, target_temp_celsius)
        return adapter.start_climatization(vehicle_id, target_temp_celsius)

    @mcp.tool(
        name="stop_climatization",
        description="Stop vehicle climate control (heating/cooling)",
        tags={"command", "climate", "comfort", "write"},
        annotations={"title": "Stop Climate Control", "readOnlyHint": False}
    )
    def stop_climatization(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> Dict[str, Any]:
        logger.info("stop climatization for id=%s", vehicle_id)
        return adapter.stop_climatization(vehicle_id)

    @mcp.tool(
        name="start_charging",
        description="Start charging the vehicle battery (BEV/PHEV only, vehicle must be plugged in)",
        tags={"command", "charging", "energy", "bev-phev", "write"},
        annotations={"title": "Start Charging", "readOnlyHint": False}
    )
    def start_charging(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> Dict[str, Any]:
        logger.info("start charging for id=%s", vehicle_id)
        return adapter.start_charging(vehicle_id)

    @mcp.tool(
        name="stop_charging",
        description="Stop charging the vehicle battery (BEV/PHEV only)",
        tags={"command", "charging", "energy", "bev-phev", "write"},
        annotations={"title": "Stop Charging", "readOnlyHint": False}
    )
    def stop_charging(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> Dict[str, Any]:
        logger.info("stop charging for id=%s", vehicle_id)
        return adapter.stop_charging(vehicle_id)

    @mcp.tool(
        name="flash_lights",
        description="Flash the vehicle lights to help locate the vehicle in a parking lot. Optional duration in seconds.",
        tags={"command", "locator", "lights", "write"},
        annotations={"title": "Flash Lights", "readOnlyHint": False}
    )
    def flash_lights(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"],
        duration_seconds: Annotated[Optional[int], "Duration in seconds (if supported by vehicle)"] = None
    ) -> Dict[str, Any]:
        logger.info("flash lights for id=%s, duration=%s", vehicle_id, duration_seconds)
        return adapter.flash_lights(vehicle_id, duration_seconds)

    @mcp.tool(
        name="honk_and_flash",
        description="Honk the horn and flash the lights to help locate the vehicle. Optional duration in seconds.",
        tags={"command", "locator", "lights", "horn", "write"},
        annotations={"title": "Honk and Flash", "readOnlyHint": False}
    )
    def honk_and_flash(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"],
        duration_seconds: Annotated[Optional[int], "Duration in seconds (if supported by vehicle)"] = None
    ) -> Dict[str, Any]:
        logger.info("honk and flash for id=%s, duration=%s", vehicle_id, duration_seconds)
        return adapter.honk_and_flash(vehicle_id, duration_seconds)

    @mcp.tool(
        name="start_window_heating",
        description="Start window heating/defrosting for front and rear windows",
        tags={"command", "climate", "comfort", "defrost", "write"},
        annotations={"title": "Start Window Heating", "readOnlyHint": False}
    )
    def start_window_heating(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> Dict[str, Any]:
        logger.info("start window heating for id=%s", vehicle_id)
        return adapter.start_window_heating(vehicle_id)

    @mcp.tool(
        name="stop_window_heating",
        description="Stop window heating/defrosting",
        tags={"command", "climate", "comfort", "defrost", "write"},
        annotations={"title": "Stop Window Heating", "readOnlyHint": False}
    )
    def stop_window_heating(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> Dict[str, Any]:
        logger.info("stop window heating for id=%s", vehicle_id)
        return adapter.stop_window_heating(vehicle_id)

def _register_ressources(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register MCP tools and resources that delegate to the adapter."""

    # Resources (read-only data access with server-side caching)
    # Note: Using readOnlyHint and idempotentHint to indicate these are safe read operations
    @mcp.resource(
        uri="data://vehicles",
        name="res_get_vehicles",
        description="List all available vehicles with VIN, name, model, and license plate",
        tags={"discovery", "read"},
        annotations={"title": "List Vehicles", "readOnlyHint": True, "idempotentHint": True}
    )
    def res_get_vehicles() -> str:
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        logger.info("Listing %d vehicles", len(vehicles))
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

    # Note: Resources would be registered here if needed
    # Currently, all functionality is provided via tools (registered in separate functions)


def _load_ai_instructions() -> str:
    """Load AI instructions from external markdown file.
    
    Returns:
        Contents of AI_INSTRUCTIONS.md or fallback message if file not found
    """
    instructions_file = Path(__file__).parent / "AI_INSTRUCTIONS.md"
    try:
        return instructions_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("AI_INSTRUCTIONS.md not found, using fallback instructions")
        return "Volkswagen WeConnect vehicle data access via MCP. Use list_vehicles to start."


def get_server(adapter: AbstractAdapter) -> FastMCP:
    """Return a FastMCP server with registered vehicle tools."""
    if not isinstance(adapter, AbstractAdapter):
        raise TypeError("adapter must be an instance of AbstractAdapter")

    # Load AI instructions from external file
    instructions = _load_ai_instructions()

    mcp = FastMCP(
        name="vehicle-service",
        instructions=instructions,
        version="1.0.0",
        auth=None,
    )
    _register_read_tools(mcp, adapter)
    _register_command_tools(mcp, adapter)
    #_register_ressources(mcp, adapter)
    return mcp

__all__ = ["get_server"]



