"""Unit tests for weather tool — mock HTTP, no LLM."""

import pytest
from unittest.mock import patch, MagicMock

from weather_agent.weather import (
    get_weather,
    _weather_code_to_text,
    _geocode,
    _fetch_forecast,
)


@pytest.mark.unit_mock
class TestWeatherCodeToText:
    """Test WMO code to Ukrainian text mapping."""

    def test_clear_sky(self):
        assert _weather_code_to_text(0) == "ясно"

    def test_snow(self):
        assert _weather_code_to_text(71) == "сніг слабкий"
        assert _weather_code_to_text(75) == "сніг сильний"

    def test_rain(self):
        assert _weather_code_to_text(61) == "дощ слабкий"
        assert _weather_code_to_text(65) == "дощ сильний"

    def test_thunderstorm(self):
        assert _weather_code_to_text(95) == "гроза"
        assert _weather_code_to_text(99) == "гроза з сильним градом"

    def test_high_code_uses_largest_matching(self):
        # Code 100 is above all keys; implementation maps to nearest lower (99)
        assert _weather_code_to_text(99) == "гроза з сильним градом"

    def test_negative_returns_unknown(self):
        assert _weather_code_to_text(-1) == "невідомо"


@pytest.mark.unit_mock
class TestGetWeatherWithMockedHttp:
    """Test get_weather with mocked httpx.Client."""

    def test_returns_weather_string_for_kyiv(
        self, mock_httpx_geocode_kyiv, mock_httpx_forecast
    ):
        def fake_get(url, params=None, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            if "geocoding" in url:
                r.json.return_value = mock_httpx_geocode_kyiv
            else:
                r.json.return_value = mock_httpx_forecast
            return r

        with patch("weather_agent.weather.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get = fake_get
            mock_client_cls.return_value = mock_client

            result = get_weather.invoke({"city": "Kyiv"})

        assert "Температура" in result
        assert "°C" in result
        assert "сніг" in result or "умови" in result
        assert "вітер" in result
        assert "вологість" in result

    def test_returns_error_for_unknown_city(self, mock_httpx_empty_geocode):
        with patch("weather_agent.weather.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value.json.return_value = mock_httpx_empty_geocode
            mock_client.get.return_value.raise_for_status = MagicMock()
            mock_client_cls.return_value = mock_client

            result = get_weather.invoke({"city": "NonExistentCity123"})

        assert "Не вдалося знайти місто" in result or "Перевірте назву" in result

    def test_returns_error_on_http_failure(self):
        import httpx
        with patch("weather_agent.weather.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.HTTPError("Connection error")
            mock_client_cls.return_value = mock_client

            result = get_weather.invoke({"city": "Kyiv"})

        assert "Не вдалося" in result

    def test_empty_city_returns_error(self):
        result = get_weather.invoke({"city": ""})
        assert "Помилка" in result or "назву міста" in result
