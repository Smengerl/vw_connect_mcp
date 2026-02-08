from fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from pathlib import Path
from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleListItem, VehicleDetailLevel, 
    ChargingModel, ClimatizationModel, MaintenanceModel, RangeModel, 
    WindowHeatingsModel, LightsModel
)
from carconnectivity.vehicle import GenericVehicle
from pydantic import BaseModel

from weconnect_mcp.cli import logging_config
logger = logging_config.get_logger(__name__)


def _register_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register MCP tools that delegate to the adapter."""

    @mcp.tool()
    def list_vehicles() -> List[Dict[str, Any]]:
        """List all vehicles with VIN, name, model, and license plate."""
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        logger.info("Listing %d vehicles", len(vehicles))
        return [v.model_dump() for v in vehicles]

    @mcp.tool()
    def get_vehicle_info(vehicle_id: str) -> Dict[str, Any]:
        """Get basic vehicle info: VIN, model, manufacturer, software, odometer, connection state.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get vehicle info for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}
        return vehicle.model_dump() if vehicle else {}

    @mcp.tool()
    def get_vehicle_state(vehicle_id: str) -> Dict[str, Any]:
        """Get complete vehicle state: position, battery, doors, windows, climate, tyres.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get vehicle state for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}
        return vehicle.model_dump() if vehicle else {}

    @mcp.tool()
    def get_vehicle_doors(vehicle_id: str) -> Dict[str, Any]:
        """Get door lock and open/closed status.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get vehicle doors for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id, components=["doors"])
        if physical_status is None or physical_status.doors is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}
        return physical_status.doors.model_dump()

    @mcp.tool()
    def get_vehicle_windows(vehicle_id: str) -> Dict[str, Any]:
        """Get window open/closed status.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get vehicle windows for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id, components=["windows"])
        if physical_status is None or physical_status.windows is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}
        return physical_status.windows.model_dump()

    @mcp.tool()
    def get_vehicle_tyres(vehicle_id: str) -> Dict[str, Any]:
        """Get tyre pressure and temperature.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get vehicle tyres for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id, components=["tyres"])
        if physical_status is None or physical_status.tyres is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}
        return physical_status.tyres.model_dump()

    @mcp.tool()
    def get_vehicle_type(vehicle_id: str) -> Dict[str, Any]:
        """Get vehicle type: electric (BEV), combustion, or hybrid (PHEV).
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get vehicle type for id=%s", vehicle_id)
        vehicle = adapter.get_vehicle(vehicle_id, details=VehicleDetailLevel.BASIC)
        if vehicle is None or vehicle.type is None:
            logger.warning("Vehicle '%s' not found or type not available", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or type not available"}
        return {"vehicle_id": vehicle_id, "type": vehicle.type}

    @mcp.tool()
    def get_charging_state(vehicle_id: str) -> Dict[str, Any]:
        """Get charging status for electric/hybrid vehicles: power, time, battery level, state.
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Note: BEV/PHEV only
        """
        logger.info("get charging state for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None or energy_status.electric is None or energy_status.electric.charging is None:
            logger.warning("Vehicle '%s' not found or doesn't support charging", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't support charging"}
        return energy_status.electric.charging.model_dump()

    @mcp.tool()
    def get_climatization_state(vehicle_id: str) -> Dict[str, Any]:
        """Get climate control: state, temperature, window/seat heating settings.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get climatization state for id=%s", vehicle_id)
        climate_status = adapter.get_climate_status(vehicle_id)
        if climate_status is None or climate_status.climatization is None:
            logger.warning("Vehicle '%s' not found or doesn't support climatization", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't support climatization"}
        return climate_status.climatization.model_dump()

    @mcp.tool()
    def get_maintenance_info(vehicle_id: str) -> Dict[str, Any]:
        """Get service schedules: inspection and oil service due dates/distances.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get maintenance info for id=%s", vehicle_id)
        maintenance_info = adapter.get_maintenance_info(vehicle_id)
        if maintenance_info is None:
            logger.warning("Vehicle '%s' not found or doesn't have maintenance info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have maintenance info"}
        return maintenance_info.model_dump()

    @mcp.tool()
    def get_range_info(vehicle_id: str) -> Dict[str, Any]:
        """Get range: total, electric (BEV/PHEV), combustion (PHEV/ICE) with battery/tank levels.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get range info for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None:
            logger.warning("Vehicle '%s' not found or doesn't have range info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have range info"}
        
        result = {"total_range_km": energy_status.range.total_km if energy_status.range else None}
        
        if energy_status.electric:
            result["electric_range_km"] = energy_status.range.electric_km if energy_status.range else None
            result["battery_level_percent"] = energy_status.electric.battery_level_percent
        
        if energy_status.combustion:
            result["combustion_range_km"] = energy_status.range.combustion_km if energy_status.range else None
            result["tank_level_percent"] = energy_status.combustion.tank_level_percent
        
        return result

    @mcp.tool()
    def get_window_heating_state(vehicle_id: str) -> Dict[str, Any]:
        """Get window heating status: front/rear on/off.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get window heating state for id=%s", vehicle_id)
        climate_status = adapter.get_climate_status(vehicle_id)
        if climate_status is None or climate_status.window_heating is None:
            logger.warning("Vehicle '%s' not found or doesn't have window heating info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have window heating info"}
        return climate_status.window_heating.model_dump()

    @mcp.tool()
    def get_lights_state(vehicle_id: str) -> Dict[str, Any]:
        """Get lights status: left/right on/off.
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get lights state for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id)
        if physical_status is None or physical_status.lights is None:
            logger.warning("Vehicle '%s' not found or doesn't have lights info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have lights info"}
        return physical_status.lights.model_dump()

    @mcp.tool()
    def get_position(vehicle_id: str) -> Dict[str, Any]:
        """Get GPS position: latitude, longitude, heading (0=N, 90=E, 180=S, 270=W).
        
        Args:
            vehicle_id: VIN, name, or license plate
        """
        logger.info("get position for id=%s", vehicle_id)
        position = adapter.get_position(vehicle_id)
        if position is None:
            logger.warning("Vehicle '%s' not found or doesn't have position info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have position info"}
        return position.model_dump()

    @mcp.tool()
    def get_battery_status(vehicle_id: str) -> Dict[str, Any]:
        """Quick battery check: level, range, charging status. Use get_charging_state for details.
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Note: BEV/PHEV only
        """
        logger.info("get battery status for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None or energy_status.electric is None:
            logger.warning("Vehicle '%s' not found or doesn't have a battery", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have a battery"}
        
        result = {
            "battery_level_percent": energy_status.electric.battery_level_percent,
            "range_km": energy_status.range.electric_km if energy_status.range else None,
            "is_charging": energy_status.electric.charging.is_charging if energy_status.electric.charging else False
        }
        
        if energy_status.electric.charging and energy_status.electric.charging.is_charging:
            result["charging_power_kw"] = energy_status.electric.charging.charging_power_kw
            result["estimated_charge_time_minutes"] = energy_status.electric.charging.remaining_time_minutes
        
        return result

    # Commands - Vehicle Control
    @mcp.tool()
    def lock_vehicle(vehicle_id: str) -> Dict[str, Any]:
        """Lock the vehicle doors.
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Returns:
            Confirmation or error message
        """
        logger.info("lock vehicle for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "lock")

    @mcp.tool()
    def unlock_vehicle(vehicle_id: str) -> Dict[str, Any]:
        """Unlock the vehicle doors.
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Returns:
            Confirmation or error message
        """
        logger.info("unlock vehicle for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "unlock")

    @mcp.tool()
    def start_climatization(vehicle_id: str, target_temperature_celsius: Optional[float] = None) -> Dict[str, Any]:
        """Start climate control/heating/cooling.
        
        Args:
            vehicle_id: VIN, name, or license plate
            target_temperature_celsius: Target temperature (optional, uses last setting if not provided)
        
        Returns:
            Confirmation or error message
        """
        logger.info("start climatization for id=%s, temp=%s", vehicle_id, target_temperature_celsius)
        return adapter.execute_command(vehicle_id, "start_climatization", target_temperature=target_temperature_celsius)

    @mcp.tool()
    def stop_climatization(vehicle_id: str) -> Dict[str, Any]:
        """Stop climate control/heating/cooling.
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Returns:
            Confirmation or error message
        """
        logger.info("stop climatization for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "stop_climatization")

    @mcp.tool()
    def start_charging(vehicle_id: str) -> Dict[str, Any]:
        """Start charging the vehicle (BEV/PHEV only).
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Returns:
            Confirmation or error message
        
        Note: Vehicle must be plugged in
        """
        logger.info("start charging for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "start_charging")

    @mcp.tool()
    def stop_charging(vehicle_id: str) -> Dict[str, Any]:
        """Stop charging the vehicle (BEV/PHEV only).
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Returns:
            Confirmation or error message
        """
        logger.info("stop charging for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "stop_charging")

    @mcp.tool()
    def flash_lights(vehicle_id: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Flash the vehicle lights (helpful for locating vehicle).
        
        Args:
            vehicle_id: VIN, name, or license plate
            duration_seconds: Optional duration (if supported by vehicle)
        
        Returns:
            Confirmation or error message
        """
        logger.info("flash lights for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "flash", duration=duration_seconds)

    @mcp.tool()
    def honk_and_flash(vehicle_id: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Honk horn and flash lights (helpful for locating vehicle).
        
        Args:
            vehicle_id: VIN, name, or license plate
            duration_seconds: Optional duration (if supported by vehicle)
        
        Returns:
            Confirmation or error message
        """
        logger.info("honk and flash for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "honk_and_flash", duration=duration_seconds)

    @mcp.tool()
    def start_window_heating(vehicle_id: str) -> Dict[str, Any]:
        """Start window heating/defrosting.
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Returns:
            Confirmation or error message
        """
        logger.info("start window heating for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "start_window_heating")

    @mcp.tool()
    def stop_window_heating(vehicle_id: str) -> Dict[str, Any]:
        """Stop window heating/defrosting.
        
        Args:
            vehicle_id: VIN, name, or license plate
        
        Returns:
            Confirmation or error message
        """
        logger.info("stop window heating for id=%s", vehicle_id)
        return adapter.execute_command(vehicle_id, "stop_window_heating")

    @mcp.resource("data://list_vehicles")
    def list_vehicles_resource() -> List[Dict[str, Any]]:
        """Return list of vehicles."""
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        logger.info("Listing %d vehicles via resource", len(vehicles))
        return [v.model_dump() for v in vehicles]

    @mcp.resource("data://state/{vehicle_id}")
    def get_vehicle_state_resource(vehicle_id: str) -> Optional[BaseModel]:
        """Return vehicle state or None if not found."""
        logger.info("get vehicle state via resource for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return None
        return vehicle


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
    _register_tools(mcp, adapter)
    return mcp

__all__ = ["get_server"]



