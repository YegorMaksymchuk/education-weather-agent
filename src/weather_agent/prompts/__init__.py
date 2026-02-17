"""Завантаження системних промптів з версіонуванням."""

from pathlib import Path

from weather_agent.config import PROMPT_VERSION

_PROMPTS_DIR = Path(__file__).resolve().parent
_FALLBACK_PROMPT = """Ти — помічник, який радить, що одягнути за погодою. Відповідай лише українською.
Завжди спочатку викликай інструмент get_weather для міста, про яке питають, потім дай коротку рекомендацію по одягу. Будь лаконічним."""


def get_system_prompt(version: str | None = None) -> str:
    """
    Повертає системний промпт для агента.
    Використовує PROMPT_VERSION з config, якщо version не передано.
    Якщо файл для версії відсутній — fallback на v1, потім на вбудований рядок.
    """
    ver = (version or PROMPT_VERSION).strip()
    filename = f"system_prompt_v{ver}.txt"
    path = _PROMPTS_DIR / filename
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    if ver != "1":
        path_v1 = _PROMPTS_DIR / "system_prompt_v1.txt"
        if path_v1.is_file():
            return path_v1.read_text(encoding="utf-8").strip()
    return _FALLBACK_PROMPT
