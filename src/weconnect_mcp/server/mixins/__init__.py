"""MCP Server Registration Functions.

Provides modular registration of MCP tools and resources.
Each module contains a single registration function for its category.
"""

from .read_tools import register_read_tools
from .command_tools import register_command_tools
from .resources import register_resources
from .prompts import register_prompts

__all__ = [
    "register_read_tools",
    "register_command_tools",
    "register_resources",
    "register_prompts",
]
