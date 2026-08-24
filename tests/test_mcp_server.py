"""
MCP Server Tests
================

This test suite validates the FastMCP MCP protocol implementation.

What is tested:
- MCP client connection to server

Test architecture:
- Uses TestAdapter for deterministic mock data
- Module-scoped fixtures for server (created once)
- Function-scoped fixtures for clients (fresh per test)
- Async tests with @pytest.mark.asyncio
- 10-second timeout per test

Fixtures (from conftest.py):
- adapter: TestAdapter with 2 mock vehicles
- mcp_server: FastMCP server instance with registered tools
- mcp_client: Connected MCP client for protocol testing

Note:
- Tool implementation tests are in tests/tools/ (not duplicated here)
- This file focuses on MCP protocol layer (Client ↔ Server connection)
"""
import pytest

import logging
logger = logging.getLogger(__name__)


# ==================== MCP CLIENT CONNECTION TESTS ====================

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_mcp_client_connects(mcp_client):
    """ Test that the MCP client can connect to the server. """
    assert mcp_client.is_connected(), "MCP client should be connected"
