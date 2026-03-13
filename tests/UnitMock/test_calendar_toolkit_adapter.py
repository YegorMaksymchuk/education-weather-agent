"""Unit tests for Google Calendar Toolkit adapter."""

from __future__ import annotations

from typing import Any, List

import pytest

from weather_agent.calendar.google_toolkit import get_calendar_tools_for_agent, _build_calendar_toolkit


class _FakeCalendarToolkit:
    def __init__(self, tools: List[Any]):
        self._tools = tools

    def get_tools(self) -> List[Any]:
        return self._tools


@pytest.mark.unit_mock
def test_get_calendar_tools_for_agent_returns_tools(monkeypatch) -> None:
    """Перевіряємо, що адаптер повертає список tools, який можна передати в create_agent."""

    class DummyTool:
        name = "dummy_calendar_tool"

    fake_toolkit = _FakeCalendarToolkit([DummyTool()])

    monkeypatch.setattr(
        "weather_agent.calendar.google_toolkit._build_calendar_toolkit",
        lambda: fake_toolkit,
    )

    tools = get_calendar_tools_for_agent()

    assert tools
    assert any(getattr(t, "name", "") == "dummy_calendar_tool" for t in tools)

