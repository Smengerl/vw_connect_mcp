"""WeConnect MCP - MCP Server for connected vehicles via the Tibber Data API.

This package provides a Model Context Protocol (MCP) server for read-only
vehicle data access. Originally built for Volkswagen, but the Tibber Data
API backend is not VW-specific -- Tibber's vehicle integration covers 30+
EV brands via Enode, so any vehicle paired to the connected Tibber account
works identically (see CLAUDE.md/ARCHITECTURE.md for the full history).

Key Components:
    - adapter: Vehicle data adapter using the Tibber Data API
    - server: MCP server implementation
    - cli: Command-line interface for running the server
"""

from importlib.metadata import PackageNotFoundError, version

try:
    # Single source of truth is the git tag (see pyproject.toml's
    # [tool.setuptools_scm]) -- this just reads back whatever setuptools_scm
    # resolved at install/build time, so there's no separate version string
    # here to drift out of sync with it.
    __version__ = version("weconnect-mcp")
except PackageNotFoundError:
    # Not installed at all (e.g. running straight from a source checkout
    # without `pip install -e .` first) -- distinct from a version genuinely
    # being unknown, which pyproject.toml's fallback_version covers instead.
    __version__ = "0.0.0+not-installed"

__all__ = [
    "__version__",
]
