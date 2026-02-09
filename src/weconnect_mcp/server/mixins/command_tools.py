"""Command Tools Registration for MCP Server.

Provides command tools for vehicle control.
All tools perform write operations that change vehicle state.
"""

from fastmcp import FastMCP
from typing import Dict, Any, Optional, Annotated

from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
from weconnect_mcp.cli import logging_config

logger = logging_config.get_logger(__name__)


def register_command_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register all command tools with the MCP server.
    
    Registers 10 command tools for vehicle control.
    
    Args:
        mcp: FastMCP server instance
        adapter: Vehicle command adapter
    """
    
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
