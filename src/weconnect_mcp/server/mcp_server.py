"""MCP Server for Volkswagen WeConnect vehicle data and control.

Provides FastMCP server with tools and resources for vehicle access.

Transport modes:
  - stdio:  Local usage with Claude Desktop / VS Code Copilot
  - http:   HTTP server for remote/cloud access (requires API key auth)

Authentication (HTTP mode):
  Set MCP_API_KEY env variable to enable Bearer token authentication.
  Without this env variable, the server runs unauthenticated (suitable
  for local use only - never expose an unauthenticated server publicly).
"""

import os
from typing import Optional

from fastmcp import FastMCP
from fastmcp.server.auth import AuthProvider
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


def _build_auth_provider(api_key: Optional[str]) -> Optional[AuthProvider]:
    """Build an auth provider from an API key, or return None for unauthenticated mode.

    Uses FastMCP's StaticTokenVerifier for simple Bearer-token authentication.
    This is suitable for self-hosted / single-user deployments.

    For production multi-user scenarios, replace with JWTVerifier + a proper
    OAuth2 / OIDC provider (e.g. Auth0, Keycloak, Authentik).

    Args:
        api_key: The secret token clients must send as `Authorization: Bearer <key>`.
                 None disables authentication entirely.

    Returns:
        A configured StaticTokenVerifier, or None.
    """
    if not api_key:
        logger.warning(
            "MCP_API_KEY is not set – server runs WITHOUT authentication. "
            "Never expose this server on a public network without an API key!"
        )
        return None

    from fastmcp.server.auth import StaticTokenVerifier

    logger.info("API-Key authentication enabled (StaticTokenVerifier)")
    return StaticTokenVerifier(
        tokens={
            api_key: {
                "client_id": "weconnect-mcp-client",
                "scopes": ["vehicles:read", "vehicles:write"],
            }
        },
        required_scopes=["vehicles:read"],
    )


def get_server(adapter: AbstractAdapter, api_key: Optional[str] = None) -> FastMCP:
    """Return a FastMCP server with registered vehicle tools and resources.
    
    Args:
        adapter: Vehicle data adapter implementing AbstractAdapter interface
        api_key: Optional Bearer token for HTTP authentication.
                 Falls back to the MCP_API_KEY environment variable if not provided.
        
    Returns:
        Configured FastMCP server instance with all tools and resources registered
        
    Raises:
        TypeError: If adapter is not an instance of AbstractAdapter
    """
    if not isinstance(adapter, AbstractAdapter):
        raise TypeError("adapter must be an instance of AbstractAdapter")

    # Resolve API key: explicit argument > env variable > None (no auth)
    resolved_api_key = api_key or os.environ.get("MCP_API_KEY")

    # Load AI instructions from external file
    instructions = _load_ai_instructions()

    auth_provider = _build_auth_provider(resolved_api_key)

    mcp = FastMCP(
        name="vehicle-service",
        instructions=instructions,
        version="1.0.0",
        auth=auth_provider,
    )
    
    # Register all MCP tools and resources
    register_read_tools(mcp, adapter)
    register_command_tools(mcp, adapter)
    #register_resources(mcp, adapter)
    register_prompts(mcp)

    # ── Health check endpoint (HTTP transport only) ───────────────────────────
    # Exposed at GET /health (unauthenticated) so that cloud platforms and load
    # balancers can verify the server is up without an API key.
    @mcp.custom_route("/health", methods=["GET", "OPTIONS"])
    async def health(_request):  # type: ignore[no-untyped-def]
        """Lightweight liveness probe – returns 200 OK when server is ready."""
        from starlette.responses import JSONResponse
        return JSONResponse({"status": "ok", "service": "weconnect-mcp"})

    return mcp


__all__ = ["get_server"]
