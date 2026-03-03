"""
ETL для GHCN-D: завантаження станцій і щоденних даних, маппінг місто→станція, генерація текстових chunks.
"""

from __future__ import annotations

import csv
import gzip
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from weather_agent.historical.chunks import DayRecord, day_record_to_ukrainian_text

# Україна bbox (приблизно)
UA_LAT_MIN, UA_LAT_MAX = 44.0, 53.0
UA_LON_MIN, UA_LON_MAX = 22.0, 41.0

# Міста для маппінгу (назва українською, lat, lon) — узгоджено з геокодом Open-Meteo
CITIES_UA: list[tuple[str, float, float]] = [
    ("Київ", 50.4501, 30.5234),
    ("Львів", 49.8397, 24.0297),
    ("Одеса", 46.4825, 30.7233),
    ("Харків", 49.9935, 36.2304),
    ("Дніпро", 48.4647, 35.0462),
    ("Запоріжжя", 47.8388, 35.1396),
    ("Вінниця", 49.2328, 28.4681),
    ("Івано-Франківськ", 48.9226, 24.7111),
    ("Чернівці", 48.2917, 25.9352),
    ("Тернопіль", 49.5535, 25.5948),
    ("Чернігів", 51.4982, 31.2893),
    ("Полтава", 49.5883, 34.5514),
    ("Суми", 50.9216, 34.8003),
    ("Миколаїв", 46.9750, 31.9946),
    ("Херсон", 46.6354, 32.6169),
    ("Черкаси", 49.4444, 32.0598),
    ("Кропивницький", 48.5132, 32.2597),
    ("Житомир", 50.2547, 28.6587),
    ("Рівне", 50.6199, 26.2516),
    ("Луцьк", 50.7593, 25.3424),
]


@dataclass
class Station:
    """Станція GHCN-D з координатами."""

    id: str
    lat: float
    lon: float
    name: str


def _parse_ghcnd_stations_line(line: str) -> Station | None:
    """
    Парсить один рядок ghcnd-stations.txt (fixed-width).
    ID 1-11, LAT 13-20, LON 22-30, ELEV 32-37, STATE 39-40, NAME 42-71, ...
    """
    if len(line) < 42:
        return None
    sid = line[0:11].strip()
    if not sid:
        return None
    try:
        lat = float(line[12:20].strip())
        lon = float(line[21:30].strip())
    except ValueError:
        return None
    name = line[41:71].strip() or sid
    return Station(id=sid, lat=lat, lon=lon, name=name)


def load_stations(path: Path | str) -> list[Station]:
    """Завантажує список станцій з ghcnd-stations.txt."""
    path = Path(path)
    stations = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            st = _parse_ghcnd_stations_line(line)
            if st and UA_LAT_MIN <= st.lat <= UA_LAT_MAX and UA_LON_MIN <= st.lon <= UA_LON_MAX:
                stations.append(st)
    return stations


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Відстань між двома точками на сфері, км."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def build_city_to_station(
    stations: list[Station],
    cities: list[tuple[str, float, float]] | None = None,
) -> dict[str, Station]:
    """Для кожного міста повертає найближчу станцію."""
    cities = cities or CITIES_UA
    out: dict[str, Station] = {}
    for city_name, clat, clon in cities:
        best: Station | None = None
        best_km = float("inf")
        for st in stations:
            d = _haversine_km(clat, clon, st.lat, st.lon)
            if d < best_km:
                best_km = d
                best = st
        if best is not None:
            out[city_name] = best
    return out


def load_ghcn_daily_csv(path: Path | str) -> Iterator[tuple[str, int, int, int, str, float, str]]:
    """
    Читає GHCN-D daily CSV (може бути .gz).
    Yields (station_id, year, month, day, element, value, q_flag).
    Колонки: ID, DATE, ELEMENT, DATA_VALUE, M_FLAG, Q_FLAG, S_FLAG, OBS_TIME.
    """
    path = Path(path)
    open_fn = gzip.open if path.suffix == ".gz" else open
    mode = "rt" if path.suffix == ".gz" else "r"
    kwargs = {"encoding": "utf-8", "errors": "replace"} if path.suffix != ".gz" else {"encoding": "utf-8"}

    with open_fn(path, mode, **kwargs) as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return
        # Можливі назви колонок
        col_id = _index_or(header, ["ID", "id"], 0)
        col_date = _index_or(header, ["DATE", "date", "YEAR/MONTH/DAY"], 1)
        col_elem = _index_or(header, ["ELEMENT", "element"], 2)
        col_val = _index_or(header, ["DATA_VALUE", "DATA VALUE", "value"], 3)
        col_q = _index_or(header, ["Q_FLAG", "Q-FLAG", "q_flag"], 5)

        for row in reader:
            if len(row) <= max(col_id, col_date, col_elem, col_val):
                continue
            sid = row[col_id].strip()
            date_str = row[col_date].strip()
            elem = row[col_elem].strip()
            q_flag = row[col_q].strip() if col_q < len(row) else ""
            if elem not in ("TMAX", "TMIN", "PRCP", "SNOW", "SNWD") or not re.match(r"^\d{8}$", date_str):
                continue
            if q_flag and q_flag not in ("", " "):  # пропускаємо сумнівні
                continue
            try:
                val = float(row[col_val])
            except (ValueError, IndexError):
                continue
            y, m, d = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
            yield (sid, y, m, d, elem, val, q_flag)


def _index_or(header: list[str], names: list[str], default: int) -> int:
    for n in names:
        try:
            return header.index(n)
        except ValueError:
            continue
    return default


def aggregate_daily_rows(
    rows: Iterator[tuple[str, int, int, int, str, float, str]],
    station_to_city: dict[str, str],
) -> Iterator[DayRecord]:
    """
    Агрегує рядки по (station_id, year, month, day) у один DayRecord.
    TMAX/TMIN — значення в десятих °C; PRCP — десятих мм; SNOW/SNWD — мм.
    """
    key_to_vals: dict[tuple[str, int, int, int], dict[str, float]] = {}
    for sid, y, m, d, elem, val, _ in rows:
        if sid not in station_to_city:
            continue
        key = (sid, y, m, d)
        if key not in key_to_vals:
            key_to_vals[key] = {}
        if elem == "TMAX" or elem == "TMIN":
            key_to_vals[key][elem] = val / 10.0  # tenths °C -> °C
        elif elem == "PRCP":
            key_to_vals[key]["prcp_mm"] = val / 10.0  # tenths mm -> mm
        elif elem == "SNOW":
            key_to_vals[key]["snow_mm"] = val
        elif elem == "SNWD":
            key_to_vals[key]["snwd_mm"] = val

    for (sid, y, m, d), vals in key_to_vals.items():
        city = station_to_city[sid]
        yield DayRecord(
            station_id=sid,
            city=city,
            year=y,
            month=m,
            day=d,
            tmax_c=vals.get("TMAX"),
            tmin_c=vals.get("TMIN"),
            prcp_mm=vals.get("prcp_mm"),
            snow_mm=vals.get("snow_mm"),
            snwd_mm=vals.get("snwd_mm"),
        )


def run_etl(
    stations_path: Path | str,
    daily_paths: list[Path | str],
    output_path: Path | str,
    cities: list[tuple[str, float, float]] | None = None,
) -> int:
    """
    Запускає ETL: станції -> маппінг місто->станція, щоденні CSV -> агрегація -> chunks CSV.
    output_path: CSV з колонками city, station_id, year, month, day, text.
    Повертає кількість записаних chunks.
    """
    stations = load_stations(stations_path)
    city_to_station = build_city_to_station(stations, cities)
    station_to_city = {st.id: city for city, st in city_to_station.items()}
    if not station_to_city:
        raise ValueError("No stations mapped to cities; check stations file and bbox.")

    def all_rows() -> Iterator[tuple[str, int, int, int, str, float, str]]:
        for p in daily_paths:
            yield from load_ghcn_daily_csv(p)

    records = aggregate_daily_rows(all_rows(), station_to_city)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["city", "station_id", "year", "month", "day", "text"])
        for rec in records:
            text = rec.to_text()
            w.writerow([rec.city, rec.station_id, rec.year, rec.month, rec.day, text])
            count += 1
    return count
