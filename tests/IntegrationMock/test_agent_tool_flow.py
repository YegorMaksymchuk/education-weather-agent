"""Integration tests: agent + get_weather with mocked HTTP, no real LLM."""

from unittest.mock import MagicMock, patch

import pytest

from weather_agent.agent import ask_agent
from weather_agent.weather import get_weather


@pytest.mark.integration_mock
class TestAgentToolIntegration:
    """Agent and tool together with mocked HTTP."""

    def test_ask_agent_with_mock_agent_calls_get_weather_and_returns_its_result(
        self, mock_httpx_geocode_kyiv, mock_httpx_forecast
    ):
        """When mock agent returns get_weather result as reply, ask_agent returns it."""
        def fake_get(url, params=None, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            r.json.return_value = (
                mock_httpx_geocode_kyiv if "geocoding" in url else mock_httpx_forecast
            )
            return r

        with patch("weather_agent.weather.httpx.Client") as mock_client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = fake_get
            mock_client_cls.return_value = client

            weather_str = get_weather.invoke({"city": "Kyiv"})
            assert "Температура" in weather_str

        fake_result = {"messages": [MagicMock(content=weather_str)]}
        with patch("weather_agent.agent._get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = fake_result
            mock_get_agent.return_value = mock_agent

            reply = ask_agent("Що одягнути в Києві?")

        assert "Температура" in reply
        assert "°C" in reply
        mock_agent.invoke.assert_called_once()

    def test_tool_contract_city_required(self):
        """get_weather validates city is non-empty."""
        out = get_weather.invoke({"city": ""})
        assert "Помилка" in out or "назву" in out

    def test_tool_contract_returns_string(self, mock_httpx_geocode_kyiv, mock_httpx_forecast):
        """get_weather returns string for valid city with mocked HTTP."""
        def fake_get(url, params=None, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            r.json.return_value = (
                mock_httpx_geocode_kyiv if "geocoding" in url else mock_httpx_forecast
            )
            return r

        with patch("weather_agent.weather.httpx.Client") as mock_client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = fake_get
            mock_client_cls.return_value = client

            out = get_weather.invoke({"city": "Lviv"})
        assert isinstance(out, str)
        assert len(out) > 0
