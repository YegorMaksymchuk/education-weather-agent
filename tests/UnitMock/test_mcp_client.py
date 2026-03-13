"""Unit tests for HttpJsonRpcMcpClient."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from weather_agent.mcp.client import HttpJsonRpcMcpClient, McpClientConfig, McpClientError


class _DummyResponse:
    def __init__(self, data: Any):
        self._data = data

    def json(self) -> Any:
        return self._data


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_mcp_client_list_tools_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """tools/list повертає список словників."""

    def fake_post(*_: Any, **__: Any) -> httpx.Response:
        return _DummyResponse(
            {
                "jsonrpc": "2.0",
                "id": "1",
                "result": [{"name": "google_calendar.listEvents"}],
            }
        )  # type: ignore[return-value]

    monkeypatch.setattr("httpx.post", fake_post)
    client = HttpJsonRpcMcpClient(McpClientConfig(endpoint="https://example.com/mcp"))

    tools = client.list_tools()
    assert tools and tools[0]["name"] == "google_calendar.listEvents"


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_mcp_client_call_tool_error_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Якщо MCP повертає error, клієнт піднімає McpClientError."""

    def fake_post(*_: Any, **__: Any) -> httpx.Response:
        return _DummyResponse(
            {
                "jsonrpc": "2.0",
                "id": "1",
                "error": {"code": 123, "message": "Tool failed"},
            }
        )  # type: ignore[return-value]

    monkeypatch.setattr("httpx.post", fake_post)
    client = HttpJsonRpcMcpClient(McpClientConfig(endpoint="https://example.com/mcp"))

    with pytest.raises(McpClientError):
        client.call_tool("google_calendar.listEvents", {"date": "2025-02-17"})


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_mcp_client_call_tool_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful call_tool returns dict result."""
    def fake_post(*_: Any, **__: Any) -> httpx.Response:
        return _DummyResponse(
            {
                "jsonrpc": "2.0",
                "id": "1",
                "result": {"events": [{"summary": "Meeting", "start": "10:00"}]},
            }
        )  # type: ignore[return-value]

    monkeypatch.setattr("httpx.post", fake_post)
    client = HttpJsonRpcMcpClient(McpClientConfig(endpoint="https://example.com/mcp"))
    result = client.call_tool("google_calendar.listEvents", {"date": "2025-02-17"})
    assert isinstance(result, dict)
    assert "events" in result
    assert len(result["events"]) == 1


class _NonJsonResponse:
    def json(self) -> Any:
        raise ValueError("Expecting value")


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_mcp_client_non_json_response_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-JSON response raises McpClientError."""
    monkeypatch.setattr("httpx.post", lambda *_, **__: _NonJsonResponse())
    client = HttpJsonRpcMcpClient(McpClientConfig(endpoint="https://example.com/mcp"))
    with pytest.raises(McpClientError, match="not valid JSON"):
        client.list_tools()


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_mcp_client_list_tools_non_list_result_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """tools/list returning non-list result raises McpClientError."""
    def fake_post(*_: Any, **__: Any) -> httpx.Response:
        return _DummyResponse({"jsonrpc": "2.0", "id": "1", "result": {}})  # type: ignore[return-value]

    monkeypatch.setattr("httpx.post", fake_post)
    client = HttpJsonRpcMcpClient(McpClientConfig(endpoint="https://example.com/mcp"))
    with pytest.raises(McpClientError, match="unexpected result"):
        client.list_tools()


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_mcp_client_call_tool_non_dict_result_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """tools/call returning non-dict result raises McpClientError."""
    def fake_post(*_: Any, **__: Any) -> httpx.Response:
        return _DummyResponse({"jsonrpc": "2.0", "id": "1", "result": []})  # type: ignore[return-value]

    monkeypatch.setattr("httpx.post", fake_post)
    client = HttpJsonRpcMcpClient(McpClientConfig(endpoint="https://example.com/mcp"))
    with pytest.raises(McpClientError, match="unexpected result"):
        client.call_tool("echo", {})


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_mcp_client_empty_endpoint_raises() -> None:
    """Empty endpoint raises McpClientError on list_tools and call_tool."""
    client = HttpJsonRpcMcpClient(McpClientConfig(endpoint=""))
    with pytest.raises(McpClientError, match="not configured"):
        client.list_tools()
    with pytest.raises(McpClientError, match="not configured"):
        client.call_tool("echo", {})

