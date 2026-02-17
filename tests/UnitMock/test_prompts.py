"""Unit tests for prompt loading — no LLM."""

import pytest

from weather_agent.prompts import get_system_prompt


@pytest.mark.unit_mock
class TestGetSystemPrompt:
    def test_v1_returns_non_empty(self):
        p = get_system_prompt(version="1")
        assert isinstance(p, str)
        assert len(p.strip()) > 0

    def test_v2_returns_non_empty_and_contains_warmth_instruction(self):
        p = get_system_prompt(version="2")
        assert isinstance(p, str)
        assert len(p.strip()) > 0
        assert "дружньому" in p or "тепло" in p

    def test_v1_contains_weather_instruction(self):
        p = get_system_prompt(version="1")
        assert "одягнути" in p or "погод" in p
        assert "get_weather" in p or "інструмент" in p

    def test_nonexistent_version_fallbacks(self):
        p = get_system_prompt(version="99")
        assert isinstance(p, str)
        assert len(p.strip()) > 0
        assert "помічник" in p or "погод" in p
