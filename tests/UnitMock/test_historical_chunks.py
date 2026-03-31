"""Unit tests for historical weather chunks — no I/O."""

import pytest

from weather_agent.historical.chunks import (
    day_record_to_ukrainian_text,
    day_record_from_dict,
    validate_month_day,
    DayRecord,
)


@pytest.mark.unit_mock
class TestDayRecordToUkrainianText:
    def test_formats_date_and_city(self):
        t = day_record_to_ukrainian_text("Київ", 1985, 3, 2, tmax_c=8.2, tmin_c=-1.1)
        assert "2 березня 1985" in t
        assert "Київ" in t
        assert "8.2" in t or "8,2" in t
        assert "-1.1" in t or "-1,1" in t

    def test_includes_precipitation(self):
        t = day_record_to_ukrainian_text(
            "Львів", 2000, 1, 15, prcp_mm=5.0, snow_mm=10.0
        )
        assert "опади" in t
        assert "сніг" in t

    def test_handles_none_values(self):
        t = day_record_to_ukrainian_text("Одеса", 1990, 6, 10)
        assert "Одеса" in t
        assert "10 червня 1990" in t


@pytest.mark.unit_mock
class TestValidateMonthDay:
    def test_valid_accepted(self):
        validate_month_day(1, 1)
        validate_month_day(12, 31)
        validate_month_day(2, 29)  # leap year day

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError, match="month"):
            validate_month_day(0, 1)
        with pytest.raises(ValueError, match="month"):
            validate_month_day(13, 1)

    def test_invalid_day_raises(self):
        with pytest.raises(ValueError, match="day"):
            validate_month_day(1, 32)
        with pytest.raises(ValueError, match="day"):
            validate_month_day(2, 30)


@pytest.mark.unit_mock
class TestDayRecordFromDict:
    def test_builds_record(self):
        row = {
            "city": "Київ",
            "year": 1985,
            "month": 3,
            "day": 2,
            "tmax_c": 8.2,
            "tmin_c": -1.1,
            "station_id": "UK000002550",
        }
        rec = day_record_from_dict(row)
        assert rec.city == "Київ"
        assert rec.year == 1985
        assert rec.month == 3
        assert rec.day == 2
        assert rec.tmax_c == 8.2
        assert rec.tmin_c == -1.1
