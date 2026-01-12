from fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
from carconnectivity.vehicle import GenericVehicle

from pydantic import BaseModel


from weconnect_mcp.cli import logging_config
logger = logging_config.get_logger(__name__)


def _register_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register tools on the provided FastMCP instance that delegate
    to the adapter. This is called once during lazy initialization.
    """

    @mcp.resource("data://list_vehicles")
    def list_vehicles() -> List[str]:
        """Return a list of available vehicles using the adapter."""
        vehicles: List[str] = adapter.list_vehicles()
        logger.info("Listing %d vehicles", len(vehicles))
        return vehicles


    @mcp.resource("data://state/{vehicle_id}")
    def get_vehicle_state(vehicle_id: str) -> BaseModel:
        """Return the state for a specific vehicle. Adapter may return
        an error dict when the vehicle is not found."""

        logger.info("get vehicle state for id=%s", vehicle_id)
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
            This server provides access to the vehicle data 
            Call list_vehicles to get an overview of available vehicles
            Call get_vehicle_state with a vehicle ID to get detailed state information
        """,
        version="1.0.0",
        auth=None,
    )
    _register_tools(mcp, adapter)
    return mcp


# Public API
__all__ = ["get_server"]



