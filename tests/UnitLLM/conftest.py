"""Fixtures for UnitLLM: fake model, mocked HTTP for get_weather."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def mock_httpx_for_weather():
    """Mock geocoding and forecast so get_weather returns without real HTTP."""
    geo = {"results": [{"latitude": 50.45, "longitude": 30.52, "timezone": "Europe/Kyiv"}]}
    forecast = {
        "current": {
            "temperature_2m": -2.0,
            "apparent_temperature": -4.0,
            "weather_code": 71,
            "wind_speed_10m": 10.0,
            "relative_humidity_2m": 80,
        }
    }

    def fake_get(url, params=None, **kwargs):
        r = MagicMock()
        r.raise_for_status = MagicMock()
        r.json.return_value = geo if "geocoding" in url else forecast
        return r

    with patch("weather_agent.weather.httpx.Client") as mock_cls:
        client = MagicMock()
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        client.get = fake_get
        mock_cls.return_value = client
        yield
