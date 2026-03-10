"""Minimal FastMCP server for integration tests: one tool (echo). Run with HTTP transport."""

from __future__ import annotations

import os
import sys

# Ensure project root on path for standalone subprocess run
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastmcp import FastMCP

mcp = FastMCP("Weather Agent MCP Test Server")


@mcp.tool
def echo(text: str) -> str:
    """Echo back the given text (for integration tests)."""
    return f"echo:{text}"


if __name__ == "__main__":
    port = int(os.environ.get("MCP_TEST_PORT", "19282"))
    mcp.run(transport="http", host="127.0.0.1", port=port)
