"""Точка входу: завантаження .env, перевірка конфігу, запуск Telegram-бота."""

import logging
import sys
from pathlib import Path

# Дозволити імпорт weather_agent при запуску з кореня проєкту (без pip install -e .)
_root = Path(__file__).resolve().parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from dotenv import load_dotenv

from weather_agent.bot import build_application
from weather_agent.config import require_openai_key, require_telegram_token

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

def main() -> None:
    load_dotenv()

    token = require_telegram_token()
    require_openai_key()
    app = build_application(token)
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
