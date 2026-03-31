"""Unit tests for get_historical_weather tool — mock Chroma/retrieval."""

from unittest.mock import MagicMock

import pytest

from weather_agent.historical.tools import get_historical_weather_impl


@pytest.mark.unit_mock
class TestGetHistoricalWeatherImpl:
    def test_empty_city_returns_error(self):
        result = get_historical_weather_impl("")
        assert "Помилка" in result or "назву міста" in result

    def test_whitespace_city_returns_error(self):
        result = get_historical_weather_impl("   ")
        assert "Помилка" in result or "назву" in result

    def test_mock_chroma_returns_chunks(self):
        mock_chroma = MagicMock()
        mock_chroma.similarity_search.return_value = [
            MagicMock(page_content="2 березня 1985, Київ: температура макс 8.2°C, мін -1.1°C."),
        ]
        getter = lambda: mock_chroma
        result = get_historical_weather_impl("Київ", chroma_getter=getter)
        assert "Історична погода" in result or "1985" in result
        assert "Київ" in result

    def test_mock_chroma_empty_returns_no_data_message(self):
        mock_chroma = MagicMock()
        mock_chroma.similarity_search.return_value = []
        result = get_historical_weather_impl("Київ", chroma_getter=lambda: mock_chroma)
        assert "не знайдено" in result or "Історичних" in result

    def test_custom_month_day_passed_to_retrieval(self):
        mock_chroma = MagicMock()
        mock_chroma.similarity_search.return_value = [
            MagicMock(page_content="15 січня 2000, Львів: макс 0°C."),
        ]
        result = get_historical_weather_impl(
            "Львів", month=1, day=15, chroma_getter=lambda: mock_chroma
        )
        call_kw = mock_chroma.similarity_search.call_args[1]
        flt = call_kw.get("filter") or {}
        assert flt.get("$and")
        and_list = flt["$and"]
        assert any(
            c.get("city", {}).get("$eq") == "Львів" for c in and_list
        ) or any(c.get("city") == "Львів" for c in and_list)
        assert any(c.get("month", {}).get("$eq") == 1 for c in and_list) or any(
            c.get("month") == 1 for c in and_list
        )
        assert any(c.get("day", {}).get("$eq") == 15 for c in and_list) or any(
            c.get("day") == 15 for c in and_list
        )
