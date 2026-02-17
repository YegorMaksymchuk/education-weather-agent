"""Shared pytest fixtures for weather agent tests."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure src is on path so weather_agent is importable
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def mock_httpx_geocode_kyiv():
    """Fake geocoding response for Kyiv."""
    return {
        "results": [
            {
                "latitude": 50.45,
                "longitude": 30.52,
                "timezone": "Europe/Kyiv",
            }
        ]
    }


@pytest.fixture
def mock_httpx_forecast():
    """Fake forecast current weather."""
    return {
        "current": {
            "temperature_2m": -2.5,
            "apparent_temperature": -4.0,
            "weather_code": 71,
            "wind_speed_10m": 15.0,
            "relative_humidity_2m": 85,
        }
    }


@pytest.fixture
def mock_httpx_empty_geocode():
    """Geocoding returns no results."""
    return {"results": []}


@pytest.fixture(autouse=True)
def env_isolate(monkeypatch):
    """Set safe defaults for optional vars. Do not delete OPENAI_API_KEY so IntegrationLLM/SystemLLM can run when set."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("PROMPT_VERSION", "2")
    monkeypatch.setenv("DEFAULT_MODEL", "gpt-4o-mini")
