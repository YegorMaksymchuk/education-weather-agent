"""
Retrieval історичної погоди: пошук за (місто, день, місяць) у ChromaDB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_chroma import Chroma

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


def retrieve_historical_same_day(
    chroma: Chroma,
    city: str,
    month: int,
    day: int,
    k: int = 5,
) -> list[str]:
    """
    Повертає топ-k текстових chunks історичної погоди для заданого міста та календарного дня.
    Використовує фільтр по metadata (city, month, day).
    """
    from weather_agent.historical.chunks import validate_month_day

    validate_month_day(month, day)
    city = (city or "").strip()
    if not city:
        return []

    where = {
        "$and": [
            {"city": {"$eq": city}},
            {"month": {"$eq": month}},
            {"day": {"$eq": day}},
        ]
    }
    query_text = f"погода {city} {day} {month} історична температура опади"
    docs = chroma.similarity_search(query_text, k=k, filter=where)
    return [d.page_content for d in docs]


def get_chroma_for_retrieval(
    persist_directory: str,
    embedding: "Embeddings",
    collection_name: str = "historical_weather",
) -> Chroma:
    """Повертає клієнт Chroma для retrieval (існуюча колекція)."""
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding,
        collection_name=collection_name,
    )
