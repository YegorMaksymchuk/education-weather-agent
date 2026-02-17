"""Завантаження конфігурації зі змінних середовища."""

import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "2")


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
