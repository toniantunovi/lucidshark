"""MCP (Model Context Protocol) integration for LucidShark.

This package provides MCP server functionality for AI agent integration,
enabling tools like Claude Code to invoke LucidShark checks.
"""

from __future__ import annotations

# These don't require the mcp library
from lucidshark.mcp.formatter import FixInstruction, InstructionFormatter
from lucidshark.mcp.tools import MCPToolExecutor
from lucidshark.mcp.watcher import LucidSharkFileWatcher


def __getattr__(name: str):
    """Lazy import for MCP server."""
    if name == "LucidSharkMCPServer":
        from lucidshark.mcp.server import LucidSharkMCPServer

        return LucidSharkMCPServer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "LucidSharkMCPServer",
    "InstructionFormatter",
    "FixInstruction",
    "MCPToolExecutor",
    "LucidSharkFileWatcher",
]
