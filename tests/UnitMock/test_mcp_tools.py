"""Unit tests for MCP-based LangChain tools (calendar)."""

from __future__ import annotations

from datetime import date as _date
from typing import Any, Mapping

import pytest

from weather_agent.mcp.client import McpClientBase, McpClientError, set_default_mcp_client
from weather_agent.mcp.tools import get_calendar_events, get_today_outdoor_blocks


class _FakeMcpClient(McpClientBase):
    def __init__(self, responses: dict[str, Any]):
        self._responses = responses

    def list_tools(self):
        return []

    def call_tool(self, name: str, arguments: Mapping[str, Any] | None = None):
        key = (name, tuple(sorted((arguments or {}).items())))
        return self._responses.get(key, {})


@pytest.fixture(autouse=True)
def _reset_mcp_client():
    """Reset default MCP client after each test to avoid leaking state."""
    yield
    set_default_mcp_client(None)


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_get_calendar_events_with_events(monkeypatch) -> None:
    today = _date.today().isoformat()
    resp_key = (
        "google_calendar.listEvents",
        (("date", today),),
    )
    fake = _FakeMcpClient(
        {
            resp_key: {
                "events": [
                    {
                        "summary": "Прогулянка в парку",
                        "start": "18:00",
                        "end": "19:30",
                        "location": "Центральний парк",
                    }
                ]
            }
        }
    )
    set_default_mcp_client(fake)

    text = get_calendar_events.invoke({})

    assert "Прогулянка в парку" in text
    assert today in text


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_get_today_outdoor_blocks_fallback_to_events(monkeypatch) -> None:
    today = _date.today().isoformat()
    resp_blocks_key = (
        "google_calendar.get_outdoor_blocks",
        (("date", today),),
    )
    resp_events_key = (
        "google_calendar.listEvents",
        (("date", today),),
    )
    fake = _FakeMcpClient(
        {
            resp_blocks_key: {"blocks": []},
            resp_events_key: {
                "events": [
                    {
                        "summary": "Поїздка на тренування",
                        "start": "07:30",
                        "end": "08:30",
                        "location": "спортзал",
                    }
                ]
            },
        }
    )
    set_default_mcp_client(fake)

    text = get_today_outdoor_blocks.invoke({})

    assert "Поїздка на тренування" in text
    assert "сьогодні" in text or today in text


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_get_calendar_events_on_mcp_error_returns_message() -> None:
    """When MCP raises McpClientError, get_calendar_events returns error message text, not exception."""

    class FailingMcpClient(McpClientBase):
        def list_tools(self):
            return []

        def call_tool(self, name: str, arguments=None):
            raise McpClientError("Server unavailable")

    set_default_mcp_client(FailingMcpClient())
    text = get_calendar_events.invoke({})
    assert "Не вдалося" in text or "помилк" in text.lower() or "MCP" in text
    assert "Server unavailable" in text or "помилк" in text.lower()


@pytest.mark.unit_mock
@pytest.mark.mcp
def test_get_calendar_events_empty_events_returns_no_events_message() -> None:
    """When MCP returns empty events list, get_calendar_events returns message about no events."""
    today = _date.today().isoformat()
    resp_key = ("google_calendar.listEvents", (("date", today),))
    fake = _FakeMcpClient({resp_key: {"events": []}})
    set_default_mcp_client(fake)
    text = get_calendar_events.invoke({})
    assert "немає подій" in text or today in text

