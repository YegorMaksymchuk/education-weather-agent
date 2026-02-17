"""Unit tests for agent with fake/mock — no real LLM API."""

from unittest.mock import MagicMock, patch

import pytest

from weather_agent.agent import ask_agent


@pytest.mark.unit_llm
class TestAskAgentResponseParsing:
    """Test ask_agent extracts final message content correctly."""

    def test_returns_final_ai_content_when_string(self):
        fake_result = {
            "messages": [
                MagicMock(),  # user
                MagicMock(content="Одягни куртку та шапку."),  # AI
            ]
        }
        with patch("weather_agent.agent._get_agent") as mock_get:
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = fake_result
            mock_get.return_value = mock_agent

            out = ask_agent("Що одягнути в Києві?")

        assert "куртку" in out
        assert "шапку" in out

    def test_returns_final_content_when_dict_message(self):
        fake_result = {
            "messages": [
                {"role": "user", "content": "?"},
                {"role": "assistant", "content": "Теплу куртку."},
            ]
        }
        with patch("weather_agent.agent._get_agent") as mock_get:
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = fake_result
            mock_get.return_value = mock_agent

            out = ask_agent("Погода в Києві?")

        assert "куртку" in out

    def test_empty_user_text_returns_prompt(self):
        out = ask_agent("")
        assert "міста" in out or "Києві" in out
        assert "Напишіть" in out or "запитай" in out

    def test_whitespace_only_returns_prompt(self):
        out = ask_agent("   ")
        assert "міста" in out or "Києві" in out
