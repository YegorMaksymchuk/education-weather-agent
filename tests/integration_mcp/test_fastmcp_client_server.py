"""Integration test: FastMCP server (subprocess) + FastMCP Client call_tool."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

import pytest

pytest.importorskip("fastmcp", reason="fastmcp not installed")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.mcp
@pytest.mark.integration_mcp
@pytest.mark.asyncio
async def test_fastmcp_client_calls_server_tool() -> None:
    """Start FastMCP test server in subprocess, call echo tool via FastMCP Client."""
    from fastmcp import Client

    port = _free_port()
    env = os.environ.copy()
    env["MCP_TEST_PORT"] = str(port)
    server_path = os.path.join(os.path.dirname(__file__), "fastmcp_test_server.py")
    proc = subprocess.Popen(
        [sys.executable, server_path],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    try:
        for _ in range(50):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(("127.0.0.1", port))
                break
            except OSError:
                time.sleep(0.1)
        else:
            pytest.fail("Server did not become ready in time")

        url = f"http://127.0.0.1:{port}/mcp"
        client = Client(url)
        async with client:
            result = await client.call_tool("echo", {"text": "hello"})

        text = None
        if hasattr(result, "content") and result.content:
            text = getattr(result.content[0], "text", None) or str(result.content[0])
        if text is None and hasattr(result, "data"):
            text = str(result.data)
        assert text is not None, f"Expected result content or data, got {result!r}"
        assert "echo:hello" in text
    finally:
        proc.terminate()
        proc.wait(timeout=5)
