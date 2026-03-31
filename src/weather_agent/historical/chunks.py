"""Форматування записів історичної погоди у текстові chunks для embedding."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from typing import Any


# Українські назви місяців (nominative)
_MONTH_NAMES_UA = [
    "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня",
]


@dataclass(frozen=True)
class DayRecord:
    """Один календарний день для однієї станції: температури та опади."""

    station_id: str
    city: str
    year: int
    month: int
    day: int
    tmax_c: float | None  # уже в °C
    tmin_c: float | None
    prcp_mm: float | None
    snow_mm: float | None
    snwd_mm: float | None

    def date_ua(self) -> str:
        """Повертає дату українською, напр. '2 березня 1985'."""
        name = _MONTH_NAMES_UA[self.month - 1]
        return f"{self.day} {name} {self.year}"

    def to_text(self) -> str:
        """Текст українською для embedding: дата, місто, показники."""
        parts = [f"{self.date_ua()}, {self.city}:"]
        if self.tmax_c is not None:
            parts.append(f" температура макс {self.tmax_c:+.1f}°C")
        if self.tmin_c is not None:
            parts.append(f" мін {self.tmin_c:+.1f}°C")
        if self.prcp_mm is not None:
            parts.append(f" опади {self.prcp_mm:.1f} мм")
        if self.snow_mm is not None:
            parts.append(f" сніг {self.snow_mm:.1f} мм")
        if self.snwd_mm is not None:
            parts.append(f" сніговий покрив {self.snwd_mm:.1f} мм")
        if len(parts) == 1:
            parts.append(" немає повних даних")
        return "".join(parts).strip() + "."


def day_record_to_ukrainian_text(
    city: str,
    year: int,
    month: int,
    day: int,
    tmax_c: float | None = None,
    tmin_c: float | None = None,
    prcp_mm: float | None = None,
    snow_mm: float | None = None,
    snwd_mm: float | None = None,
    station_id: str = "",
) -> str:
    """
    Формує один текстовий chunk українською для одного дня та міста.
    Використовується в ETL та при ручній збірці документів.
    """
    rec = DayRecord(
        station_id=station_id,
        city=city,
        year=year,
        month=month,
        day=day,
        tmax_c=tmax_c,
        tmin_c=tmin_c,
        prcp_mm=prcp_mm,
        snow_mm=snow_mm,
        snwd_mm=snwd_mm,
    )
    return rec.to_text()


def day_record_from_dict(row: dict[str, Any]) -> DayRecord:
    """Збирає DayRecord з словника (наприклад з DataFrame/CSV)."""
    return DayRecord(
        station_id=str(row.get("station_id", "")),
        city=str(row["city"]),
        year=int(row["year"]),
        month=int(row["month"]),
        day=int(row["day"]),
        tmax_c=float(row["tmax_c"]) if row.get("tmax_c") is not None else None,
        tmin_c=float(row["tmin_c"]) if row.get("tmin_c") is not None else None,
        prcp_mm=float(row["prcp_mm"]) if row.get("prcp_mm") is not None else None,
        snow_mm=float(row["snow_mm"]) if row.get("snow_mm") is not None else None,
        snwd_mm=float(row["snwd_mm"]) if row.get("snwd_mm") is not None else None,
    )


def validate_month_day(month: int, day: int) -> None:
    """Перевіряє коректність (month, day); інакше ValueError."""
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1-12, got {month}")
    max_day = calendar.monthrange(2000, month)[1]  # 2000 — високосний для лютого
    if not 1 <= day <= max_day:
        raise ValueError(f"day for month {month} must be 1-{max_day}, got {day}")
