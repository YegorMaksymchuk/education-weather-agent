"""Завантаження конфігурації зі змінних середовища."""

import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "2")

# ChromaDB / historical weather RAG
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "chroma_langchain_db")
CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "historical_weather")
OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# MCP / external tools integration
_mcp_ep = os.getenv("MCP_ENDPOINT")
MCP_ENDPOINT: str | None = _mcp_ep.strip() if _mcp_ep and _mcp_ep.strip() else None
MCP_TIMEOUT_SECONDS: float = float(os.getenv("MCP_TIMEOUT_SECONDS", "10"))

# Google Calendar (LangChain CalendarToolkit) — ті самі змінні для локального запуску та Docker (шляхи в контейнері зазвичай /app/secrets/...)
_gc_cred = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
GOOGLE_CALENDAR_CREDENTIALS_PATH: str | None = (
    _gc_cred.strip() if _gc_cred and _gc_cred.strip() else None
)
_gc_tok = os.getenv("GOOGLE_CALENDAR_TOKEN_PATH")
GOOGLE_CALENDAR_TOKEN_PATH: str | None = (
    _gc_tok.strip() if _gc_tok and _gc_tok.strip() else None
)

# Observability (OpenLIT / OpenTelemetry)
_otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
OTEL_EXPORTER_OTLP_ENDPOINT: str | None = (
    _otel_endpoint.strip() if _otel_endpoint and _otel_endpoint.strip() else None
)
OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "weather-agent")
OTEL_DEPLOYMENT_ENVIRONMENT: str = os.getenv("OTEL_DEPLOYMENT_ENVIRONMENT", "development")
# OpenLIT: у SDK передається як capture_message_content (OTEL: OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT)
_genai_capture = os.getenv("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT")
OPENLIT_TRACE_CONTENT: bool = (
    _genai_capture.strip().lower() == "true"
    if _genai_capture is not None and _genai_capture.strip() != ""
    else os.getenv("OPENLIT_TRACE_CONTENT", "true").lower() == "true"
)


def require_telegram_token() -> str:
    """Повертає токен бота; якщо відсутній — викликає SystemExit."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_BOT_TOKEN.strip():
        raise SystemExit("Встановіть TELEGRAM_BOT_TOKEN у .env або середовищі.")
    return TELEGRAM_BOT_TOKEN.strip()


def require_openai_key() -> str:
    """Повертає OpenAI API ключ; якщо відсутній — викликає SystemExit."""
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        raise SystemExit("Встановіть OPENAI_API_KEY у .env або середовищі.")
    return OPENAI_API_KEY.strip()
