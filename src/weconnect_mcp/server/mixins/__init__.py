"""MCP Server Registration Functions.

Provides modular registration of MCP tools.
Each module contains a single registration function for its category.
"""

from .read_tools import register_read_tools
from .prompts import register_prompts

__all__ = [
    "register_read_tools",
    "register_prompts",
]
