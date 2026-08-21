"""Command Tools Registration for MCP Server.

Provides command tools for vehicle control.

With the Tibber backend, none of these commands are functional: the
Tibber Data API is read-only (confirmed via its OpenAPI schema — no
command/write endpoint exists at all, see
experiment/tibber-integration/TIBBER_API.md §5). Every tool below always
returns {"success": false, "error": "Not supported: the Tibber Data API is
read-only (no command endpoints exist)."} regardless of vehicle or
parameters. They stay registered (rather than being removed) so that an
MCP client gets a clear, structured "not supported" response instead of
the tool not existing at all.
"""

from fastmcp import FastMCP
from typing import Dict, Any, Optional, Annotated

from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
from weconnect_mcp.cli import logging_config

logger = logging_config.get_logger(__name__)


def register_command_tools(mcp: FastMCP, adapter: AbstractAdapter) -> None:
    """Register all command tools with the MCP server.

    Registers 10 command tools for vehicle control. With the Tibber
    backend, all 10 always return a "not supported" result — the Tibber
    Data API has no write endpoints (see module docstring).

    Args:
        mcp: FastMCP server instance
        adapter: Vehicle command adapter
    """

    @mcp.tool(
        name="lock_vehicle",
        description="NOT SUPPORTED with the Tibber backend (read-only API, no lock/unlock endpoint). Always returns success: false.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no lock/unlock endpoint). Always returns success: false.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no climate-control endpoint). Always returns success: false.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no climate-control endpoint). Always returns success: false.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no charging-control endpoint). Always returns success: false. Use get_charging_status to read the current state instead.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no charging-control endpoint). Always returns success: false. Use get_charging_status to read the current state instead.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no locator endpoint). Always returns success: false.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no locator endpoint). Always returns success: false.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no window-heating endpoint). Always returns success: false.",
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
        description="NOT SUPPORTED with the Tibber backend (read-only API, no window-heating endpoint). Always returns success: false.",
        tags={"command", "climate", "comfort", "defrost", "write"},
        annotations={"title": "Stop Window Heating", "readOnlyHint": False}
    )
    def stop_window_heating(
        vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
    ) -> Dict[str, Any]:
        logger.info("stop window heating for id=%s", vehicle_id)
        return adapter.stop_window_heating(vehicle_id)
