"""Точка входу: завантаження .env, перевірка конфігу, запуск Telegram-бота."""

import logging
import os
import sys
from pathlib import Path

# Дозволити імпорт weather_agent при запуску з кореня проєкту (без pip install -e .)
_root = Path(__file__).resolve().parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from dotenv import load_dotenv

load_dotenv()

# До openlit.init: httpx-трейси без URL Telegram (у шляху getUpdates є секрет бота).
_httpx_excl = os.getenv("OTEL_PYTHON_HTTPX_EXCLUDED_URLS")
if _httpx_excl is None or not _httpx_excl.strip():
    os.environ["OTEL_PYTHON_HTTPX_EXCLUDED_URLS"] = r"api\.telegram\.org"

import openlit

from weather_agent.config import (
    OTEL_DEPLOYMENT_ENVIRONMENT,
    OTEL_EXPORTER_OTLP_ENDPOINT,
    OTEL_SERVICE_NAME,
    OPENLIT_TRACE_CONTENT,
    require_openai_key,
    require_telegram_token,
)

# OpenLIT має ініціалізуватися ДО імпорту bot → agent → LangChain (автоінструментація).
# У новіших версіях openlit: capture_message_content (раніше інколи trace_content).
openlit.init(
    otlp_endpoint=OTEL_EXPORTER_OTLP_ENDPOINT,
    application_name=OTEL_SERVICE_NAME,
    service_name=OTEL_SERVICE_NAME,
    environment=OTEL_DEPLOYMENT_ENVIRONMENT,
    capture_message_content=OPENLIT_TRACE_CONTENT,
)

from weather_agent.bot import build_application  # noqa: E402

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

_logger = logging.getLogger(__name__)
if OTEL_EXPORTER_OTLP_ENDPOINT:
    _logger.info("OpenTelemetry OTLP export enabled: %s", OTEL_EXPORTER_OTLP_ENDPOINT)
else:
    _logger.warning(
        "OpenTelemetry OTLP export disabled (OTEL_EXPORTER_OTLP_ENDPOINT unset). "
        "Use http://localhost:4318 for local runs with `make observability-up`, "
        "or rely on Docker Compose env for weather-agent."
    )


def main() -> None:
    load_dotenv()

    token = require_telegram_token()
    require_openai_key()
    app = build_application(token)
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
