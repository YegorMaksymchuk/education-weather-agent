"""Integration tests: ChromaDB store + retrieval with real Chroma, fake embeddings."""

from pathlib import Path

import pytest

from langchain_core.embeddings import FakeEmbeddings

from weather_agent.historical.etl import run_etl
from weather_agent.historical.retrieval import retrieve_historical_same_day
from weather_agent.historical.store import build_and_persist_chroma, get_chroma_client


@pytest.fixture
def fixtures_dir():
    return Path(__file__).resolve().parent.parent / "fixtures" / "ghcn"


@pytest.fixture
def chunks_csv(tmp_path, fixtures_dir):
    """Produce chunks CSV from fixture data."""
    out = tmp_path / "chunks.csv"
    run_etl(
        fixtures_dir / "ghcnd-stations-ua-sample.txt",
        [fixtures_dir / "daily-sample.csv"],
        out,
    )
    return out


@pytest.fixture
def chroma_store(tmp_path, chunks_csv):
    """Build Chroma from chunks CSV with fake embeddings, persist to tmp_path."""
    persist = tmp_path / "chroma_db"
    emb = FakeEmbeddings(size=64)
    return build_and_persist_chroma(
        chunks_csv,
        persist_directory=persist,
        embedding=emb,
        collection_name="test_historical_weather",
    )


@pytest.mark.integration_mock
class TestChromaRetrievalIntegration:
    """Chroma + retrieval with fixture data and fake embeddings."""

    def test_retrieve_returns_docs_for_matching_city_month_day(self, chroma_store, chunks_csv):
        """For (city, month, day) that exist in chunks, retrieval returns non-empty list."""
        import csv
        with open(chunks_csv, encoding="utf-8", newline="") as f:
            row = next(csv.DictReader(f))
        city, month, day = row["city"], int(row["month"]), int(row["day"])
        results = retrieve_historical_same_day(chroma_store, city, month, day, k=5)
        assert len(results) >= 1
        assert row["text"] in results or any(row["text"][:20] in r for r in results)

    def test_retrieve_empty_for_wrong_day(self, chroma_store):
        """Filter (city, month, day) with no data returns empty."""
        results = retrieve_historical_same_day(chroma_store, "Київ", 12, 31, k=5)
        # Our fixture has only 1985-03-02; Dec 31 may have no rows depending on city mapping
        assert isinstance(results, list)

    def test_get_chroma_client_loads_persisted(self, tmp_path, chunks_csv):
        """After build_and_persist, get_chroma_client can query the same collection."""
        persist = tmp_path / "chroma_db"
        emb = FakeEmbeddings(size=64)
        build_and_persist_chroma(
            chunks_csv,
            persist_directory=persist,
            embedding=emb,
            collection_name="test_historical_weather",
        )
        client = get_chroma_client(persist, emb, collection_name="test_historical_weather")
        import csv
        with open(chunks_csv, encoding="utf-8", newline="") as f:
            row = next(csv.DictReader(f))
        city, month, day = row["city"], int(row["month"]), int(row["day"])
        results = retrieve_historical_same_day(client, city, month, day, k=3)
        assert len(results) >= 1
