"""
ChromaDB колекція та індексація з ETL-виводу (CSV chunks).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma


def load_chunks_csv(csv_path: Path | str) -> list[Document]:
    """
    Завантажує chunks з CSV (колонки: city, station_id, year, month, day, text)
    у список LangChain Document з metadata city, month, day, year.
    """
    path = Path(csv_path)
    docs = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text", "").strip()
            if not text:
                continue
            meta: dict[str, Any] = {
                "city": (row.get("city") or "").strip(),
                "month": int(row.get("month", 0)),
                "day": int(row.get("day", 0)),
                "year": int(row.get("year", 0)),
            }
            docs.append(Document(page_content=text, metadata=meta))
    return docs


def build_and_persist_chroma(
    chunks_csv_path: Path | str,
    persist_directory: Path | str,
    embedding: Embeddings,
    collection_name: str = "historical_weather",
) -> Chroma:
    """
    Створює колекцію Chroma з документів у CSV та зберігає в persist_directory.
    Повертає інстанс Chroma для подальших запитів.
    """
    docs = load_chunks_csv(chunks_csv_path)
    if not docs:
        raise ValueError(f"No documents loaded from {chunks_csv_path}")
    persist_dir = str(Path(persist_directory).resolve())
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    return Chroma.from_documents(
        docs,
        embedding,
        persist_directory=persist_dir,
        collection_name=collection_name,
    )


def get_chroma_client(
    persist_directory: Path | str,
    embedding: Embeddings,
    collection_name: str = "historical_weather",
) -> Chroma:
    """
    Підключається до існуючої колекції Chroma (persist_directory).
    Якщо колекція порожня, повертає клієнт без документів.
    """
    persist_dir = str(Path(persist_directory).resolve())
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding,
        collection_name=collection_name,
    )
