from fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter, VehicleListItem, ChargingModel
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
        """List all available vehicles. Returns a list of vehicle information including VIN, name, and model.
        Use the VIN field to identify vehicles in other tool calls."""
        vehicles: List[VehicleListItem] = adapter.list_vehicles()
        logger.info("Listing %d vehicles", len(vehicles))
        return [v.model_dump() for v in vehicles]

    @mcp.tool()
    def get_vehicle_state(vehicle_id: str) -> Dict[str, Any]:
        """Get the complete state of a specific vehicle.
        
        Args:
            vehicle_id: The ID of the vehicle to query
            
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
            vehicle_id: The ID of the vehicle to query
            
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
            - list_vehicles: Get a list of all available vehicles with VIN, name, and model
            - get_vehicle_state: Get complete state of a vehicle (battery, position, doors, windows, climate, tyres)
            - get_vehicle_doors: Get door lock and open/closed status
            - get_vehicle_windows: Get window open/closed status
            - get_vehicle_tyres: Get tyre pressure and temperature
            - get_vehicle_type: Get the vehicle type (electric/BEV, combustion, hybrid)
            - get_charging_state: Get detailed charging information for electric/hybrid vehicles
            
            Start by calling list_vehicles to see available vehicles. When referring to vehicles, 
            use their name if available (more user-friendly), but always use the VIN as the vehicle_id 
            parameter when calling other tools.
            
            For charging information, use get_charging_state to get details about:
            - Whether the vehicle is currently charging
            - Charging power and estimated completion time
            - Battery level and target charge percentage
            
            All tools except list_vehicles require a vehicle_id parameter (which should be the VIN).
        """,
        version="1.0.0",
        auth=None,
    )
    _register_tools(mcp, adapter)
    return mcp


# Public API
__all__ = ["get_server"]



