"""
Shared Test Fixtures for All MCP Tests
=======================================

This module provides pytest fixtures that are automatically available to all test files
in the tests/ directory and subdirectories via pytest's conftest.py mechanism.

Fixtures provided:
- adapter: TestAdapter instance with 2 mock vehicles for testing
- mcp_server: FastMCP server instance with all tools, commands, and resources registered
- mcp_client: Connected MCP client for async resource/tool access testing

Usage:
Tests can simply declare these fixtures as function parameters:

    # In tools/commands tests:
    def test_something(adapter):
        vehicles = adapter.list_vehicles()
        assert len(vehicles) == 2
    
    # In any test:
    def test_server(mcp_server):
        tools = await mcp_server.get_tools()
        assert "list_vehicles" in tools
    
    # In resources tests (async):
    async def test_resource(mcp_client):
        result = await mcp_client.read_resource("data://list_vehicles")
        assert result is not None

Benefits:
- No duplication of fixture code across test directories
- Centralized fixture management in one location
- Easy to update fixtures for all tests at once
- Consistent fixtures across tools/, commands/, and resources/
- Async client handling with automatic connect/disconnect

Architecture:
- adapter: Provides mock vehicle data (TestAdapter)
- mcp_server: Uses adapter to create FastMCP server instance
- mcp_client: Connects to mcp_server for protocol testing
"""
import pytest
import sys
from pathlib import Path
from fastmcp import Client

# Add tests directory to Python path for imports
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from test_adapter import TestAdapter
from weconnect_mcp.server.mcp_server import get_server


@pytest.fixture
def adapter():
    """Provide a TestAdapter instance with 2 mock vehicles for testing.
    
    Available for all tests in tools/, commands/, and resources/.
    
    Returns:
        TestAdapter with:
        - ID.7 Tourer (electric, VIN: WVWZZZED4SE003938)
        - Transporter 7 (combustion, VIN: WV2ZZZSTZNH009136)
    """
    return TestAdapter()


@pytest.fixture
def mcp_server(adapter):
    """Provide a FastMCP server instance with all tools, commands, and resources registered.
    
    Uses the adapter fixture to create a fully configured MCP server.
    
    Available for:
    - Tool registration tests
    - Command registration tests
    - Resource registration tests
    - Direct server access tests
    
    Args:
        adapter: TestAdapter instance (injected by pytest)
    
    Returns:
        FastMCP server instance with all endpoints registered
    """
    return get_server(adapter)


@pytest.fixture
async def mcp_client(mcp_server):
    """Provide a connected MCP client for async resource/tool access testing.
    
    Function-scoped: fresh client per test to avoid state pollution.
    Automatically connects and disconnects via async context manager.
    
    Available for:
    - Resource read tests (read_resource)
    - Tool invocation tests (call_tool)
    - MCP protocol tests
    
    Args:
        mcp_server: FastMCP server instance (injected by pytest)
    
    Yields:
        Connected MCP Client instance
    
    Usage:
        @pytest.mark.asyncio
        async def test_example(mcp_client):
            result = await mcp_client.read_resource("data://list_vehicles")
    """
    async with Client(mcp_server) as client:
        yield client
