"""Shared pytest fixtures for weather agent tests."""

import inspect
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _otel_tests_export_enabled() -> bool:
    """When true, pytest sends OTLP (OpenLIT) so traces/metrics can appear in Grafana after tests."""
    return os.getenv("OTEL_TESTS_EXPORT", "").strip().lower() in ("1", "true", "yes")


# Default: no OTLP during pytest (avoids noise and accidental export).
# Opt-in: OTEL_TESTS_EXPORT=1 and optional OTEL_EXPORTER_OTLP_ENDPOINT (defaults to http://localhost:4318).
if not _otel_tests_export_enabled():
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""
else:
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip():
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318"
    if not os.environ.get("OTEL_SERVICE_NAME", "").strip():
        os.environ["OTEL_SERVICE_NAME"] = "weather-agent-tests"
    if not os.environ.get("OTEL_DEPLOYMENT_ENVIRONMENT", "").strip():
        os.environ["OTEL_DEPLOYMENT_ENVIRONMENT"] = "test"
    # Same as main.py: do not put Telegram bot token in traces.
    _hx = os.getenv("OTEL_PYTHON_HTTPX_EXCLUDED_URLS")
    if _hx is None or not _hx.strip():
        os.environ["OTEL_PYTHON_HTTPX_EXCLUDED_URLS"] = r"api\.telegram\.org"

    def _init_openlit_for_tests() -> None:
        import openlit

        from weather_agent.config import (
            OTEL_DEPLOYMENT_ENVIRONMENT,
            OTEL_EXPORTER_OTLP_ENDPOINT,
            OTEL_SERVICE_NAME,
            OPENLIT_TRACE_CONTENT,
        )

        init_kw: dict = {
            "otlp_endpoint": OTEL_EXPORTER_OTLP_ENDPOINT,
            "application_name": OTEL_SERVICE_NAME,
            "service_name": OTEL_SERVICE_NAME,
            "environment": OTEL_DEPLOYMENT_ENVIRONMENT,
            "capture_message_content": OPENLIT_TRACE_CONTENT,
        }
        sig = inspect.signature(openlit.init)
        if "disable_batch" in sig.parameters:
            init_kw["disable_batch"] = True
        openlit.init(**init_kw)

    _init_openlit_for_tests()


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
    monkeypatch.setenv("PROMPT_VERSION", "3")
    monkeypatch.setenv("DEFAULT_MODEL", "gpt-4o-mini")
    if not _otel_tests_export_enabled():
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
