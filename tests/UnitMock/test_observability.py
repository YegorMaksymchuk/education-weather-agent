"""Тести конфігурації та ініціалізації OpenLIT (без відправки OTLP)."""

import os

import pytest

import weather_agent.config as config


@pytest.mark.unit_mock
def test_otel_config_defaults_when_endpoint_empty():
    """Без endpoint експорт OTLP вимкнено (None після strip)."""
    if os.getenv("OTEL_TESTS_EXPORT", "").strip().lower() in ("1", "true", "yes"):
        pytest.skip("OTEL_TESTS_EXPORT увімкнено — endpoint може бути заданий для експорту в Grafana")
    assert config.OTEL_EXPORTER_OTLP_ENDPOINT is None
    assert config.OTEL_SERVICE_NAME == "weather-agent"
    assert config.OTEL_DEPLOYMENT_ENVIRONMENT == "development"
    assert isinstance(config.OPENLIT_TRACE_CONTENT, bool)


@pytest.mark.unit_mock
def test_openlit_package_importable():
    """Пакет openlit встановлений; init викликається лише в main.py (щоб не дублювати глобальний стан OTel у тестах)."""
    openlit = pytest.importorskip("openlit")
    assert callable(getattr(openlit, "init", None))
