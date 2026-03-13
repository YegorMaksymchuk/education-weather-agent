"""LangChain tools поверх MCP (наприклад, Google Calendar).

Ці інструменти не прив'язані до Telegram: їх можна використовувати в будь-якому
клієнті, який викликає наш LangChain-агент.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from typing import Any, Iterable

from langchain_core.tools import tool

from weather_agent.mcp.client import McpClientError, McpClientBase, get_default_mcp_client


@dataclass(slots=True)
class _CalendarEvent:
    summary: str
    start: str
    end: str | None = None
    location: str | None = None


def _parse_events(raw: Any) -> list[_CalendarEvent]:
    """Перетворює довільну MCP-відповідь у внутрішній формат подій.

    Очікуваний формат result:
      {"events": [{"summary": "...", "start": "...", "end": "...", "location": "..."}, ...]}
    У тестах це можна контролювати через fake MCP-клієнт.
    """
    if not isinstance(raw, dict):
        return []
    events_data = raw.get("events") or []
    events: list[_CalendarEvent] = []
    for item in events_data:
        if not isinstance(item, dict):
            continue
        summary = str(item.get("summary") or "").strip()
        start = str(item.get("start") or "").strip()
        if not summary or not start:
            continue
        events.append(
            _CalendarEvent(
                summary=summary,
                start=start,
                end=str(item.get("end")).strip() if item.get("end") else None,
                location=str(item.get("location")).strip()
                if item.get("location")
                else None,
            )
        )
    return events


def _format_events_text(events: Iterable[_CalendarEvent], header: str) -> str:
    lines = [header]
    for ev in events:
        time_part = ev.start
        if ev.end:
            time_part = f"{ev.start}–{ev.end}"
        loc_part = f" (місце: {ev.location})" if ev.location else ""
        lines.append(f"- {time_part}: {ev.summary}{loc_part}")
    return "\n".join(lines)


def _get_client() -> McpClientBase:
    return get_default_mcp_client()


@tool
def get_calendar_events(date_iso: str | None = None) -> str:
    """Отримати події з календаря на вказану дату (ISO формат YYYY-MM-DD, за замовчуванням сьогодні).

    Використовується агентом, щоб доповнити пораду по одягу контекстом розкладу
    (наприклад, довгі прогулянки, поїздки, зустрічі поза домом).
    """
    target_date = _date.fromisoformat(date_iso) if date_iso else _date.today()
    try:
        client = _get_client()
        result = client.call_tool(
            "google_calendar.listEvents",
            {"date": target_date.isoformat()},
        )
        events = _parse_events(result)
    except McpClientError as exc:
        return (
            "Не вдалося отримати події з календаря через помилку MCP-сервера: "
            f"{exc!s}. Продовжую без урахування розкладу."
        )
    except Exception:
        return (
            "Сталася неочікувана помилка при зверненні до календаря. "
            "Продовжую без урахування розкладу."
        )

    if not events:
        return f"У календарі немає подій на {target_date.isoformat()}."

    return _format_events_text(
        events,
        header=f"Події у вашому календарі на {target_date.isoformat()}:",
    )


@tool
def get_today_outdoor_blocks() -> str:
    """Оцінити інтервали дня, коли ви, ймовірно, будете надворі (за даними календаря).

    Викликається агентом, щоб краще поєднати погоду та ваші плани (наприклад,
    якщо ввечері довга прогулянка, а вдень — робота в офісі).
    """
    today = _date.today()
    try:
        client = _get_client()
        result = client.call_tool(
            "google_calendar.get_outdoor_blocks",
            {"date": today.isoformat()},
        )
        blocks = result.get("blocks") if isinstance(result, dict) else None
        if not blocks:
            # Фолбек: якщо спеціального інструмента немає, використовуємо listEvents.
            events_result = client.call_tool(
                "google_calendar.listEvents", {"date": today.isoformat()}
            )
            events = _parse_events(events_result)
            if not events:
                return (
                    "За календарем немає подій, які б явно вимагали перебування надворі сьогодні."
                )
            return (
                "На основі подій у календарі:\n"
                + _format_events_text(
                    events,
                    header="Можливі інтервали, коли ви будете надворі сьогодні:",
                )
            )
    except McpClientError as exc:
        return (
            "Не вдалося оцінити зовнішні активності за календарем через помилку MCP-сервера: "
            f"{exc!s}. Продовжую без урахування розкладу."
        )
    except Exception:
        return (
            "Сталася неочікувана помилка при аналізі календаря. "
            "Продовжую без урахування зовнішніх активностей."
        )

    if not isinstance(blocks, list) or not blocks:
        return (
            "За календарем немає явних інтервалів, коли ви будете надворі сьогодні."
        )

    lines = ["Інтервали, коли ви, ймовірно, будете надворі сьогодні:"]
    for block in blocks:
        if not isinstance(block, dict):
            continue
        start = str(block.get("start") or "").strip()
        end = str(block.get("end") or "").strip()
        reason = str(block.get("reason") or "").strip()
        if not start:
            continue
        interval = f"{start}–{end}" if end else start
        if reason:
            lines.append(f"- {interval}: {reason}")
        else:
            lines.append(f"- {interval}")

    return "\n".join(lines)

