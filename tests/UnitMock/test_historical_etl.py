"""Unit tests for GHCN-D ETL — use local fixtures, no network."""

import csv
import tempfile
from pathlib import Path

import pytest

from weather_agent.historical.etl import (
    load_stations,
    build_city_to_station,
    load_ghcn_daily_csv,
    run_etl,
    Station,
)


@pytest.fixture
def fixtures_dir():
    return Path(__file__).resolve().parent.parent / "fixtures" / "ghcn"


@pytest.fixture
def stations_path(fixtures_dir):
    return fixtures_dir / "ghcnd-stations-ua-sample.txt"


@pytest.fixture
def daily_path(fixtures_dir):
    return fixtures_dir / "daily-sample.csv"


@pytest.mark.unit_mock
class TestLoadStations:
    def test_parses_ua_stations(self, stations_path):
        stations = load_stations(stations_path)
        assert len(stations) >= 2
        ids = [s.id for s in stations]
        assert "UK000002550" in ids
        assert "UK000003350" in ids
        by_id = {s.id: s for s in stations}
        assert by_id["UK000002550"].lat == 50.4
        assert by_id["UK000002550"].lon == 30.55

    def test_empty_file_returns_empty(self, tmp_path):
        (tmp_path / "empty.txt").write_text("")
        assert load_stations(tmp_path / "empty.txt") == []


@pytest.mark.unit_mock
class TestBuildCityToStation:
    def test_kyiv_maps_to_nearest(self, stations_path):
        stations = load_stations(stations_path)
        city_to_st = build_city_to_station(stations)
        assert "Київ" in city_to_st
        assert city_to_st["Київ"].id == "UK000002550"
        assert "Львів" in city_to_st
        assert city_to_st["Львів"].id == "UK000003350"


@pytest.mark.unit_mock
class TestLoadGhcnDailyCsv:
    def test_yields_element_rows(self, daily_path):
        rows = list(load_ghcn_daily_csv(daily_path))
        assert len(rows) >= 5
        tmax = [r for r in rows if r[4] == "TMAX"]
        assert len(tmax) >= 1
        assert tmax[0][0] == "UK000002550"
        assert tmax[0][1] == 1985 and tmax[0][2] == 3 and tmax[0][3] == 2
        assert tmax[0][5] == 82  # tenths °C

    def test_converts_tmin_tmax_tenths(self, daily_path):
        rows = list(load_ghcn_daily_csv(daily_path))
        tmax = next(r for r in rows if r[4] == "TMAX" and r[0] == "UK000002550")
        assert tmax[5] == 82


@pytest.mark.unit_mock
class TestRunEtl:
    def test_produces_chunks_csv(self, stations_path, daily_path, tmp_path):
        out = tmp_path / "chunks.csv"
        n = run_etl(stations_path, [daily_path], out)
        assert n >= 1
        assert out.is_file()
        with open(out, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == n
        assert "city" in rows[0] and "text" in rows[0]
        cities = [r["city"] for r in rows]
        assert len(cities) >= 1
        # ETL maps stations to cities by nearest; fixture has UK stations -> some UA city names
        assert any("1985" in r["text"] or "березня" in r["text"] or "март" in r["text"] for r in rows)
