"""
Shared Test Fixtures for MCP Tool Tests
========================================

This module provides pytest fixtures that are automatically available to all test files
in the tests/tools/ directory via pytest's conftest.py mechanism.

Fixtures provided:
- adapter: TestAdapter instance with 2 mock vehicles for testing
- mcp_server: FastMCP server instance with all tools registered

Usage:
Tests can simply declare these fixtures as function parameters:
    def test_something(adapter):
        vehicles = adapter.list_vehicles()
        assert len(vehicles) == 2

Benefits:
- No duplication of fixture code across test files
- Centralized fixture management
- Easy to update fixtures for all tool tests
"""
import pytest

from test_adapter import TestAdapter
from weconnect_mcp.server.mcp_server import get_server


@pytest.fixture
def adapter():
    """Provide a TestAdapter instance for all tool tests."""
    return TestAdapter()


@pytest.fixture
def mcp_server(adapter):
    """Provide an MCP server instance for tool registration tests."""
    return get_server(adapter)
