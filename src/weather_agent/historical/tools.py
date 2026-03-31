"""Tool для агента: історична погода в цей день (RAG з ChromaDB)."""

from __future__ import annotations

from datetime import date
from typing import Callable

from langchain_core.tools import tool

from weather_agent.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    OPENAI_EMBEDDING_MODEL,
)
from weather_agent.historical.retrieval import get_chroma_for_retrieval, retrieve_historical_same_day


_chroma_client = None


def _get_chroma():
    """Лінива ініціалізація Chroma клієнта (потрібен OPENAI_API_KEY для embedding)."""
    global _chroma_client
    if _chroma_client is None:
        from langchain_openai import OpenAIEmbeddings

        from weather_agent.config import require_openai_key

        require_openai_key()
        emb = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
        _chroma_client = get_chroma_for_retrieval(
            CHROMA_PERSIST_DIR,
            emb,
            collection_name=CHROMA_COLLECTION_NAME,
        )
    return _chroma_client


def get_historical_weather_impl(
    city: str,
    month: int | None = None,
    day: int | None = None,
    k: int = 5,
    chroma_getter: Callable[[], object] | None = None,
) -> str:
    """
    Реалізація retrieval історичної погоди для тестування та tool.
    Якщо month/day не передано — використовується сьогоднішня дата.
    """
    if not city or not city.strip():
        return "Помилка: не вказано назву міста."
    today = date.today()
    m = month if month is not None else today.month
    d = day if day is not None else today.day
    try:
        chroma = (chroma_getter or _get_chroma)()
        # Спочатку пробуємо знайти записи саме для цього календарного дня.
        chunks = retrieve_historical_same_day(chroma, city.strip(), m, d, k=k)
    except Exception:
        return f"Не вдалося отримати історичні дані погоди для «{city.strip()}». Можливо, база історичних даних ще не заповнена або місто не підтримується."
    if not chunks:
        # Фолбек: якщо на цей день немає записів, пробуємо будь-які історичні
        # приклади для міста (без фільтру по дню/місяцю).
        try:
            query_text = f"погода {city.strip()} історична температура опади"
            city_filter = {"city": {"$eq": city.strip()}}
            docs = chroma.similarity_search(query_text, k=k, filter=city_filter)
            chunks = [d.page_content for d in docs]
        except Exception:
            # Якщо навіть фолбек не спрацьовує — повертаємо попередження.
            return f"Історичних записів погоди для «{city.strip()}» на цей день ({d}.{m}) не знайдено."

    if not chunks:
        return (
            f"Історичних записів погоди для «{city.strip()}» на цей день ({d}.{m}) "
            "та загалом по місту не знайдено."
        )

    header = (
        f"Історична погода в цей день ({d}.{m}) (приклади з минулих років):"
        if any(
            f"{d} " in c and city.strip() in c
            for c in chunks
        )
        else "Історична погода для цього міста (найближчі наявні приклади з минулих років):"
    )
    return " " + header + "\n" + "\n".join(f"- {c}" for c in chunks)


@tool
def get_historical_weather(city: str) -> str:
    """Отримати історичні приклади погоди в цей день для міста (порівняння з минулими роками). Викликай після get_weather, якщо хочеш додати порівняння «цей день в історії» до рекомендації що одягнути."""
    return get_historical_weather_impl(city)
