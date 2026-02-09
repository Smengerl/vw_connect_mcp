"""MCP Server for Volkswagen WeConnect vehicle data and control.

Provides FastMCP server with tools and resources for vehicle access.
"""

from fastmcp import FastMCP
from pathlib import Path

from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
from weconnect_mcp.server.mixins import (
    register_read_tools,
    register_command_tools,
    register_resources,
    register_prompts,
)
from weconnect_mcp.cli import logging_config

logger = logging_config.get_logger(__name__)


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
    """Return a FastMCP server with registered vehicle tools and resources.
    
    Args:
        adapter: Vehicle data adapter implementing AbstractAdapter interface
        
    Returns:
        Configured FastMCP server instance with all tools and resources registered
        
    Raises:
        TypeError: If adapter is not an instance of AbstractAdapter
    """
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
    
    # Register all MCP tools and resources
    register_read_tools(mcp, adapter)
    register_command_tools(mcp, adapter)
    #register_resources(mcp, adapter)
    register_prompts(mcp)
    
    return mcp


__all__ = ["get_server"]
