"""Unit tests for bot welcome/help texts — no LLM."""

import pytest

from weather_agent.bot import WELCOME_TEXT, HELP_TEXT


@pytest.mark.unit_mock
class TestBotTexts:
    def test_welcome_non_empty(self):
        assert isinstance(WELCOME_TEXT, str)
        assert len(WELCOME_TEXT.strip()) > 0

    def test_welcome_contains_example(self):
        assert "Києві" in WELCOME_TEXT or "одягнути" in WELCOME_TEXT

    def test_help_non_empty(self):
        assert isinstance(HELP_TEXT, str)
        assert len(HELP_TEXT.strip()) > 0

    def test_help_contains_commands(self):
        assert "/start" in HELP_TEXT
        assert "/help" in HELP_TEXT

    def test_help_contains_example_queries(self):
        assert "Києві" in HELP_TEXT or "Львові" in HELP_TEXT or "Одесі" in HELP_TEXT
