"""
Shared Test Fixtures for All MCP Tests
=======================================

This module provides pytest fixtures that are automatically available to all test files
in the tests/ directory and subdirectories via pytest's conftest.py mechanism.

Fixtures provided:

Mock Data Fixtures (for unit/integration tests):
- adapter: TestAdapter instance with 2 mock vehicles (module-scoped)
- mcp_server: FastMCP server with TestAdapter (module-scoped)
- mcp_client: Connected MCP client for async testing (function-scoped)

Real API Fixtures (for end-to-end tests):
- config_path: Path to VW account credentials (src/config.json)
- tokenstore_file: Path to OAuth token cache (tmp/tokenstore)
- real_adapter: CarConnectivityAdapter connected to real VW API (module-scoped)
- real_mcp_server: FastMCP server with real adapter running in background (module-scoped)
- real_mcp_client: MCP client connected to real server (function-scoped)

Usage:
Tests can simply declare these fixtures as function parameters:

    # In tools/commands/resources/test_mcp_server.py (mock data):
    def test_something(adapter):
        vehicles = adapter.list_vehicles()
        assert len(vehicles) == 2
    
    async def test_mcp_protocol(mcp_client):
        result = await mcp_client.read_resource("data://list_vehicles")
    
    # In test_carconnectivity_adapter.py (real API):
    async def test_real_api(real_adapter):
        vehicles = await real_adapter.list_vehicles()
        assert len(vehicles) > 0
    
    # In test_full_roundtrip.py (real end-to-end):
    async def test_roundtrip(real_mcp_client):
        result = await real_mcp_client.read_resource("data://list_vehicles")

Benefits:
- No duplication of fixture code across test files
- Centralized fixture management in one location
- Easy to update fixtures for all tests at once
- Consistent fixtures across all test types
- Async client handling with automatic connect/disconnect
- Both mock and real API fixtures available

Architecture:
- Mock fixtures use TestAdapter for fast, deterministic tests
- Real fixtures use CarConnectivityAdapter for integration tests
- Module-scoped fixtures for expensive resources (adapters, servers)
- Function-scoped clients for test isolation
"""
import pytest
import sys
import asyncio
import logging
from pathlib import Path
from fastmcp import Client
from collections.abc import AsyncIterator

# Add tests directory to Python path for imports
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from test_adapter import TestAdapter
from weconnect_mcp.server.mcp_server import get_server
from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter

logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


# ==================== MOCK DATA FIXTURES ====================

@pytest.fixture(scope="module")
def adapter():
    """Provide a TestAdapter instance with 2 mock vehicles for testing.
    
    Module-scoped: Created once per test module and reused across all tests.
    
    Available for all tests in:
    - tools/
    - commands/
    - resources/
    - test_mcp_server.py
    
    Returns:
        TestAdapter with:
        - ID.7 Tourer (electric, VIN: WVWZZZED4SE003938)
        - Transporter 7 (combustion, VIN: WV2ZZZSTZNH009136)
    """
    return TestAdapter()


@pytest.fixture(scope="module")
def mcp_server(adapter):
    """Provide a FastMCP server instance with all tools, commands, and resources registered.
    
    Module-scoped: Created once per test module and reused across all tests.
    
    Uses the adapter fixture to create a fully configured MCP server.
    
    Available for:
    - Tool registration tests
    - Command registration tests
    - Resource registration tests
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
    """Provide a connected MCP client for async resource/tool access testing.
    
    Function-scoped: Fresh client per test to avoid state pollution.
    Automatically connects and disconnects via async context manager.
    
    Available for:
    - Resource read tests (read_resource)
    - Tool invocation tests (call_tool)
    - MCP protocol tests (test_mcp_server.py)
    
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


# ==================== REAL API FIXTURES ====================

@pytest.fixture(scope="module")
def config_path() -> Path:
    """Provide path to VW account credentials configuration.
    
    Returns path to src/config.json containing:
    - VW account username
    - VW account password
    - Other CarConnectivity settings
    
    Located at: ../src/config.json (relative to tests directory)
    
    Used by:
    - test_carconnectivity_adapter.py
    - test_full_roundtrip.py
    """
    current_dir = Path(__file__).resolve().parent
    return (current_dir / "../src/config.json").resolve()


@pytest.fixture(scope="module")
def tokenstore_file() -> Path:
    """Provide path to OAuth token cache file.
    
    Returns path to tokenstore file for caching VW API OAuth tokens.
    Avoids repeated logins across test runs.
    
    Located at: ../tmp/tokenstore (relative to tests directory)
    
    Used by:
    - test_carconnectivity_adapter.py
    - test_full_roundtrip.py
    """
    current_dir = Path(__file__).resolve().parent
    return (current_dir / "../tmp/tokenstore").resolve()


@pytest.fixture(scope="module")
async def real_adapter(
    config_path: Path,
    tokenstore_file: Path,
) -> AsyncIterator[CarConnectivityAdapter]:
    """Provide a CarConnectivityAdapter connected to real VW API.
    
    Module-scoped: Logs in once per test session, reuses connection.
    
    Lifecycle:
    1. Reads credentials from config_path
    2. Connects to VW API (uses tokenstore if available)
    3. Yields authenticated adapter to tests
    4. Automatically disconnects on teardown
    
    Used by:
    - test_carconnectivity_adapter.py
    - test_full_roundtrip.py (via real_mcp_server)
    
    Returns:
        Authenticated CarConnectivityAdapter instance
    """
    logger.debug("1/7 Entering real_adapter fixture")
    async with CarConnectivityAdapter(
        config_path.as_posix(),
        tokenstore_file.as_posix(),
    ) as adapter_instance:
        yield adapter_instance
    logger.debug("7/7 Exiting real_adapter fixture")


@pytest.fixture(scope="module")
async def real_mcp_server(config_path: Path, real_adapter: CarConnectivityAdapter):
    """Provide a FastMCP server running with real CarConnectivityAdapter.
    
    Module-scoped: Server is created once and runs in background for all tests.
    
    Lifecycle:
    1. Creates server with real VW API adapter
    2. Starts server in background asyncio task
    3. Runs stdio transport for MCP protocol
    4. Yields server to tests
    5. Cancels task and waits for clean shutdown
    
    Used by:
    - test_full_roundtrip.py
    
    Note: Server runs continuously; clients connect/disconnect per test.
    """
    logger.debug("2/7 Entering real_mcp_server fixture")
    server = get_server(real_adapter)
    finished = asyncio.Event()

    async def run_and_signal():
        try:
            await server.run_stdio_async(show_banner=False)
        finally:
            finished.set()

    task = asyncio.create_task(run_and_signal())
    await asyncio.sleep(1)  # Give server time to start
    try:
        yield server
    finally:
        logger.debug("5/7 Exiting real_mcp_server fixture - start")
        task.cancel()
        await finished.wait()
        logger.debug("6/7 Exiting real_mcp_server fixture")


@pytest.fixture(scope="function")
async def real_mcp_client(real_mcp_server):
    """Provide a connected MCP client for testing server communication with real API.
    
    Function-scoped: Fresh client per test to ensure isolated test state.
    
    Uses async context manager for automatic connection and disconnection.
    Each test gets a new client connected to the long-running server.
    
    Used by:
    - test_full_roundtrip.py
    """
    logger.debug("3/7 Entering real_mcp_client fixture")
    async with Client(real_mcp_server) as client:
        yield client
    logger.debug("4/7 Exiting real_mcp_client fixture")
