from fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter, VehicleListItem, ChargingModel, ClimatizationModel, MaintenanceModel, RangeModel, WindowHeatingsModel, LightsModel
from carconnectivity.vehicle import GenericVehicle

from pydantic import BaseModel


from weconnect_mcp.cli import logging_config
logger = logging_config.get_logger(__name__)


def _register_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register tools on the provided FastMCP instance that delegate
    to the adapter. This is called once during lazy initialization.
    """

    # Register as TOOLS (not resources) so AI can call them
    @mcp.tool()
    def list_vehicles() -> List[Dict[str, Any]]:
        """List all available vehicles. Returns a list of vehicle information including VIN, name, model, and license plate.
        Use the VIN, name, or license plate to identify vehicles in other tool calls."""
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        logger.info("Listing %d vehicles", len(vehicles))
        return [v.model_dump() for v in vehicles]

    @mcp.tool()
    def get_vehicle_info(vehicle_id: str) -> Dict[str, Any]:
        """Get basic vehicle information including software version, model year, and connection state.
        
        Args:
            vehicle_id: Vehicle identifier - can be VIN, name, or license plate
            
        Returns:
            Vehicle information including VIN, model, name, manufacturer, odometer, state, 
            type, software version, model year, and connection state
        """
        logger.info("get vehicle info for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}

        return vehicle.model_dump() if vehicle else {}

    @mcp.tool()
    def get_vehicle_state(vehicle_id: str) -> Dict[str, Any]:
        """Get the complete state of a specific vehicle.
        
        Args:
            vehicle_id: Vehicle identifier - can be VIN, name, or license plate
            
        Returns:
            Complete vehicle information including position, battery, doors, windows, climate, and tyres
        """
        logger.info("get vehicle state for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}

        return vehicle.model_dump() if vehicle else {}

    @mcp.tool()
    def get_vehicle_doors(vehicle_id: str) -> Dict[str, Any]:
        """Get the door status of a specific vehicle.
        
        Args:
            vehicle_id: Vehicle identifier - can be VIN, name, or license plate
            
        Returns:
            Door states including lock status and open/closed state for all doors
        """
        logger.info("get vehicle doors for id=%s", vehicle_id)
        doors = adapter.get_doors_state(vehicle_id)
        if doors is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}
        
        return doors.model_dump() if doors else {}

    @mcp.tool()
    def get_vehicle_windows(vehicle_id: str) -> Dict[str, Any]:
        """Get the window status of a specific vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Window states for all windows (open/closed)
        """
        logger.info("get vehicle windows for id=%s", vehicle_id)
        windows = adapter.get_windows_state(vehicle_id)
        if windows is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}
        
        return windows.model_dump() if windows else {}

    @mcp.tool()
    def get_vehicle_tyres(vehicle_id: str) -> Dict[str, Any]:
        """Get the tyre status of a specific vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Tyre pressure and temperature for all tyres
        """
        logger.info("get vehicle tyres for id=%s", vehicle_id)
        tyres = adapter.get_tyres_state(vehicle_id)
        if tyres is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found"}
        
        return tyres.model_dump() if tyres else {}

    @mcp.tool()
    def get_vehicle_type(vehicle_id: str) -> Dict[str, Any]:
        """Get the type of a specific vehicle (e.g., electric, combustion, hybrid).
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Vehicle type information. Common types include:
            - 'electric': Battery Electric Vehicle (BEV)
            - 'combustion': Internal Combustion Engine vehicle
            - 'hybrid': Hybrid Electric Vehicle (HEV/PHEV)
        """
        logger.info("get vehicle type for id=%s", vehicle_id)
        vehicle_type = adapter.get_vehicle_type(vehicle_id)
        if vehicle_type is None:
            logger.warning("Vehicle '%s' not found or type not available", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or type not available"}
        
        return {"vehicle_id": vehicle_id, "type": vehicle_type}

    @mcp.tool()
    def get_charging_state(vehicle_id: str) -> Dict[str, Any]:
        """Get the current charging status of an electric or hybrid vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Detailed charging information including:
            - is_charging: Whether the vehicle is currently charging
            - is_plugged_in: Whether the charging cable is connected
            - charging_power_kw: Current charging power in kilowatts
            - charging_state: Current state (charging, ready, off, error)
            - remaining_time_minutes: Estimated minutes until fully charged
            - target_soc_percent: Target state of charge percentage
            - current_soc_percent: Current battery level percentage
            - charge_mode: Charging mode (manual, timer, etc.)
            
        Note: Only available for electric (BEV) and plug-in hybrid (PHEV) vehicles.
        """
        logger.info("get charging state for id=%s", vehicle_id)
        charging_state = adapter.get_charging_state(vehicle_id)
        if charging_state is None:
            logger.warning("Vehicle '%s' not found or doesn't support charging", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't support charging"}
        
        return charging_state.model_dump()

    @mcp.tool()
    def get_climatization_state(vehicle_id: str) -> Dict[str, Any]:
        """Get the current climate control status of a vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Climate control information including:
            - state: Current state (off, heating, cooling, ventilation)
            - is_active: Whether climate control is currently active
            - target_temperature_celsius: Target temperature in Celsius
            - estimated_time_remaining_minutes: Time until target temperature reached
            - window_heating_enabled: Is window heating enabled
            - seat_heating_enabled: Is seat heating enabled
            - climatization_at_unlock_enabled: Start climatization when unlocking
            - using_external_power: Is using external power (not battery)
        """
        logger.info("get climatization state for id=%s", vehicle_id)
        climate_status = adapter.get_climate_status(vehicle_id)
        if climate_status is None or climate_status.climatization is None:
            logger.warning("Vehicle '%s' not found or doesn't support climatization", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't support climatization"}
        
        return climate_status.climatization.model_dump()

    @mcp.tool()
    def get_maintenance_info(vehicle_id: str) -> Dict[str, Any]:
        """Get the maintenance and service information for a vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Maintenance information including:
            - inspection_due_date: Next inspection due date (ISO format)
            - inspection_due_distance_km: Remaining kilometers until inspection
            - oil_service_due_date: Next oil service due date (ISO format)
            - oil_service_due_distance_km: Remaining kilometers until oil service
            
        Note: Oil service information is only available for combustion and hybrid vehicles.
        """
        logger.info("get maintenance info for id=%s", vehicle_id)
        maintenance_info = adapter.get_maintenance_info(vehicle_id)
        if maintenance_info is None:
            logger.warning("Vehicle '%s' not found or doesn't have maintenance info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have maintenance info"}
        
        return maintenance_info.model_dump()

    @mcp.tool()
    def get_range_info(vehicle_id: str) -> Dict[str, Any]:
        """Get the range and energy information for a vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Range information including:
            - total_range_km: Total remaining range in kilometers
            - electric_range_km: Electric range (for BEV/PHEV)
            - battery_level_percent: Battery charge percentage (for BEV/PHEV)
            - combustion_range_km: Combustion range (for PHEV/ICE)
            - tank_level_percent: Fuel tank level (for PHEV/ICE)
        """
        logger.info("get range info for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None:
            logger.warning("Vehicle '%s' not found or doesn't have range info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have range info"}
        
        # Extract range information from energy status
        result = {
            "total_range_km": energy_status.range.total_km if energy_status.range else None
        }
        
        if energy_status.electric:
            result["electric_range_km"] = energy_status.range.electric_km if energy_status.range else None
            result["battery_level_percent"] = energy_status.electric.battery_level_percent
        
        if energy_status.combustion:
            result["combustion_range_km"] = energy_status.range.combustion_km if energy_status.range else None
            result["tank_level_percent"] = energy_status.combustion.tank_level_percent
        
        return result

    @mcp.tool()
    def get_window_heating_state(vehicle_id: str) -> Dict[str, Any]:
        """Get the window heating status of a vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Window heating information including:
            - front: Front window heating status (on/off)
            - rear: Rear window heating status (on/off)
        """
        logger.info("get window heating state for id=%s", vehicle_id)
        climate_status = adapter.get_climate_status(vehicle_id)
        if climate_status is None or climate_status.window_heating is None:
            logger.warning("Vehicle '%s' not found or doesn't have window heating info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have window heating info"}
        
        return climate_status.window_heating.model_dump()

    @mcp.tool()
    def get_lights_state(vehicle_id: str) -> Dict[str, Any]:
        """Get the lights status of a vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Lights information including:
            - left: Left light status (on/off)
            - right: Right light status (on/off)
        """
        logger.info("get lights state for id=%s", vehicle_id)
        physical_status = adapter.get_physical_status(vehicle_id)
        if physical_status is None or physical_status.lights is None:
            logger.warning("Vehicle '%s' not found or doesn't have lights info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have lights info"}
        
        return physical_status.lights.model_dump()

    @mcp.tool()
    def get_position(vehicle_id: str) -> Dict[str, Any]:
        """Get the current GPS position of a vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Position information including:
            - latitude: GPS latitude in decimal degrees
            - longitude: GPS longitude in decimal degrees
            - heading: Compass heading in degrees (0-360, 0=North, 90=East, 180=South, 270=West)
        """
        logger.info("get position for id=%s", vehicle_id)
        position = adapter.get_position(vehicle_id)
        if position is None:
            logger.warning("Vehicle '%s' not found or doesn't have position info", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have position info"}
        
        return position.model_dump()

    @mcp.tool()
    def get_battery_status(vehicle_id: str) -> Dict[str, Any]:
        """Get the battery status of an electric or hybrid vehicle.
        
        This is a simplified tool for quick battery and range checks.
        For detailed charging information, use get_charging_state instead.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
        Returns:
            Battery status including:
            - battery_level_percent: Current battery charge (0-100%)
            - range_km: Remaining electric range in kilometers
            - is_charging: Whether currently charging
            - charging_power_kw: Charging power (only when charging)
            - estimated_charge_time_minutes: Time to full charge (only when charging)
            
        Note: Only available for electric (BEV) and plug-in hybrid (PHEV) vehicles.
        """
        logger.info("get battery status for id=%s", vehicle_id)
        energy_status = adapter.get_energy_status(vehicle_id)
        if energy_status is None or energy_status.electric is None:
            logger.warning("Vehicle '%s' not found or doesn't have a battery", vehicle_id)
            return {"error": f"Vehicle {vehicle_id} not found or doesn't have a battery"}
        
        # Extract battery information from energy status
        result = {
            "battery_level_percent": energy_status.electric.battery_level_percent,
            "range_km": energy_status.range.electric_km if energy_status.range else None,
            "is_charging": energy_status.electric.charging.is_charging if energy_status.electric.charging else False
        }
        
        # Add charging details if currently charging
        if energy_status.electric.charging and energy_status.electric.charging.is_charging:
            result["charging_power_kw"] = energy_status.electric.charging.charging_power_kw
            result["estimated_charge_time_minutes"] = energy_status.electric.charging.remaining_time_minutes
        
        return result


    # Also keep resources for direct data access
    @mcp.resource("data://list_vehicles")
    def list_vehicles_resource() -> List[Dict[str, Any]]:
        """Return a list of available vehicles using the adapter."""
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        logger.info("Listing %d vehicles via resource", len(vehicles))
        return [v.model_dump() for v in vehicles]

    @mcp.resource("data://state/{vehicle_id}")
    def get_vehicle_state_resource(vehicle_id: str) -> BaseModel:
        """Return the state for a specific vehicle. Adapter may return
        an error dict when the vehicle is not found."""
        logger.info("get vehicle state via resource for id=%s", vehicle_id)
        vehicle: Optional[BaseModel] = adapter.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Vehicle '%s' not found", vehicle_id)
            return BaseModel()

        return vehicle



def get_server(adapter: AbstractAdapter) -> FastMCP:
    """Return a FastMCP server.
    The function requires an instance of a class deriving from
    `AbstractAdapter`. 
    """
    if not isinstance(adapter, AbstractAdapter):
        raise TypeError("adapter must be an instance of AbstractAdapter")

    mcp = FastMCP(
        name="vehicle-service",
        instructions="""
            This server provides access to Volkswagen vehicle data via MCP tools.
            
            Available tools:
            - list_vehicles: Get a list of all available vehicles with VIN, name, model, and license plate
            - get_vehicle_info: Get basic vehicle information (software version, model year, connection state)
            - get_vehicle_state: Get complete state of a vehicle (battery, position, doors, windows, climate, tyres)
            - get_vehicle_doors: Get door lock and open/closed status
            - get_vehicle_windows: Get window open/closed status
            - get_vehicle_tyres: Get tyre pressure and temperature
            - get_vehicle_type: Get the vehicle type (electric/BEV, combustion, hybrid)
            - get_charging_state: Get detailed charging information for electric/hybrid vehicles
            - get_climatization_state: Get climate control status (heating/cooling, temperature, settings)
            - get_maintenance_info: Get maintenance schedules (inspection and oil service due dates/distances)
            - get_range_info: Get range information (total, electric, and combustion ranges with battery/tank levels)
            - get_window_heating_state: Get window heating status (front and rear windows)
            - get_lights_state: Get vehicle lights status (left and right lights)
            
            Start by calling list_vehicles to see available vehicles. Vehicle can be identified by
            name (preferred), VIN, or license plate in all tools.
            
            For electric/hybrid vehicles, you can use:
            - get_charging_state for charging information
            - get_range_info for battery level and electric range
            
            For climate control and comfort:
            - get_climatization_state to check if heating/cooling is active and target temperature
            - get_window_heating_state to check if window heating is on
            
            For safety:
            - get_lights_state to check if any lights were left on
            
            For maintenance, use get_maintenance_info to see when the next service is due.
            
            All tools except list_vehicles require a vehicle_id parameter (which should be the VIN).
        """,
        version="1.0.0",
        auth=None,
    )
    _register_tools(mcp, adapter)
    return mcp


# Public API
__all__ = ["get_server"]



