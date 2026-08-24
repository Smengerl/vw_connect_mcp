"""
Shared Test Fixtures for All MCP Tests
=======================================

This module provides pytest fixtures that are automatically available to all test files
in the tests/ directory and subdirectories via pytest's conftest.py mechanism.

Fixtures provided:

- adapter: TestAdapter instance with 2 mock vehicles (module-scoped)
- mcp_server: FastMCP server with TestAdapter (module-scoped)
- mcp_client: Connected MCP client for async testing (function-scoped)

Usage:
Tests can simply declare these fixtures as function parameters:

    def test_something(adapter):
        vehicles = adapter.list_vehicles()
        assert len(vehicles) == 2

    async def test_mcp_protocol(mcp_client):
        result = await mcp_client.call_tool("get_vehicles")

Benefits:
- No duplication of fixture code across test files
- Centralized fixture management in one location
- Easy to update fixtures for all tests at once
- Async client handling with automatic connect/disconnect

Architecture:
- Fixtures use TestAdapter for fast, deterministic tests
- Module-scoped fixtures for expensive resources (adapters, servers)
- Function-scoped clients for test isolation
"""
import pytest
import sys
import logging
from pathlib import Path
from fastmcp import Client

# Add tests directory to Python path for imports
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from test_adapter import TestAdapter
from weconnect_mcp.server.mcp_server import get_server

logger = logging.getLogger(__name__)


# ==================== MOCK DATA FIXTURES ====================

@pytest.fixture(scope="module")
def adapter():
    """Provide a TestAdapter instance with 2 mock vehicles for testing.

    Module-scoped: Created once per test module and reused across all tests.

    Available for all tests in:
    - tools/
    - test_mcp_server.py

    Returns:
        TestAdapter with:
        - ID.7 Tourer (electric, VIN: WVWZZZED4SE003938)
        - T7 Multivan eHybrid (hybrid, VIN: WV2ZZZSTZNH009136)
    """
    return TestAdapter()


@pytest.fixture(scope="module")
def mcp_server(adapter):
    """Provide a FastMCP server instance with all tools and prompts registered.

    Module-scoped: Created once per test module and reused across all tests.

    Uses the adapter fixture to create a fully configured MCP server.

    Available for:
    - Tool registration tests
    - Direct server access tests
    - MCP protocol tests (test_mcp_server.py)

    Args:
        adapter: TestAdapter instance (injected by pytest)

    Returns:
        FastMCP server instance with all endpoints registered
    """
    return get_server(adapter)


@pytest.fixture(scope="function")
async def mcp_client(mcp_server):
    """Provide a connected MCP client for async tool-call testing.

    Function-scoped: Fresh client per test to avoid state pollution.
    Automatically connects and disconnects via async context manager.

    Available for:
    - Tool invocation tests (call_tool)
    - MCP protocol tests (test_mcp_server.py)

    Args:
        mcp_server: FastMCP server instance (injected by pytest)

    Yields:
        Connected MCP Client instance

    Usage:
        @pytest.mark.asyncio
        async def test_example(mcp_client):
            result = await mcp_client.call_tool("get_vehicles")
    """
    async with Client(mcp_server) as client:
        yield client
