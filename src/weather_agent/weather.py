"""Open-Meteo клієнт та tool get_weather для агента."""

import httpx
from langchain_core.tools import tool

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HTTP_TIMEOUT = 15.0

# WMO Weather interpretation codes (WW) -> короткий опис українською
WMO_WEATHER_UA = {
    0: "ясно",
    1: "переважно ясно",
    2: "помірна хмарність",
    3: "хмарно",
    45: "туман",
    48: "інійний туман",
    51: "морось слабка",
    53: "морось помірна",
    55: "морось сильна",
    56: "замерзаюча морось слабка",
    57: "замерзаюча морось сильна",
    61: "дощ слабкий",
    63: "дощ помірний",
    65: "дощ сильний",
    66: "замерзаючий дощ слабкий",
    67: "замерзаючий дощ сильний",
    71: "сніг слабкий",
    73: "сніг помірний",
    75: "сніг сильний",
    77: "сніжні зерна",
    80: "злива слабка",
    81: "злива помірна",
    82: "злива сильна",
    85: "снігова злива слабка",
    86: "снігова злива сильна",
    95: "гроза",
    96: "гроза з невеликим градом",
    99: "гроза з сильним градом",
}


def _weather_code_to_text(code: int) -> str:
    """Перетворює WMO код погоди на опис українською."""
    if code in WMO_WEATHER_UA:
        return WMO_WEATHER_UA[code]
    for threshold in sorted(WMO_WEATHER_UA.keys(), reverse=True):
        if code >= threshold:
            return WMO_WEATHER_UA[threshold]
    return "невідомо"


def _geocode(city: str) -> tuple[float, float, str] | None:
    """Повертає (latitude, longitude, timezone) для першого результату пошуку міста."""
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                GEOCODING_URL,
                params={"name": city.strip(), "count": 1, "language": "uk"},
            )
            r.raise_for_status()
            data = r.json()
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        return None

    results = data.get("results")
    if not results:
        return None

    first = results[0]
    lat = first.get("latitude")
    lon = first.get("longitude")
    tz = first.get("timezone", "UTC")
    if lat is None or lon is None:
        return None
    return (float(lat), float(lon), str(tz))


def _fetch_forecast(lat: float, lon: float, timezone: str) -> dict | None:
    """Отримує поточну погоду з Open-Meteo Forecast API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "weather_code",
            "wind_speed_10m",
            "apparent_temperature",
        ],
    }
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(FORECAST_URL, params=params)
            r.raise_for_status()
            return r.json()
    except (httpx.HTTPError, httpx.TimeoutException):
        return None


@tool
def get_weather(city: str) -> str:
    """Отримати поточну погоду для міста (назва українською або англійською). Використовуй для рекомендацій що одягнути."""
    if not city or not city.strip():
        return "Помилка: не вказано назву міста."

    coords = _geocode(city.strip())
    if not coords:
        return f"Не вдалося знайти місто «{city.strip()}». Перевірте назву або спробуйте інший варіант."

    lat, lon, tz = coords
    data = _fetch_forecast(lat, lon, tz)
    if not data:
        return f"Не вдалося отримати погоду для «{city.strip()}». Спробуйте пізніше."

    current = data.get("current")
    if not current:
        return f"Немає даних про поточну погоду для «{city.strip()}»."

    temp = current.get("temperature_2m")
    feels = current.get("apparent_temperature")
    code = current.get("weather_code", 0)
    wind = current.get("wind_speed_10m")
    humidity = current.get("relative_humidity_2m")

    temp_str = f"{temp:+.1f}°C" if temp is not None else "—"
    feels_str = f"{feels:+.1f}°C" if feels is not None else ""
    cond = _weather_code_to_text(int(code))
    wind_str = f"{wind:.0f} км/год" if wind is not None else "—"
    hum_str = f"{humidity:.0f}%" if humidity is not None else "—"

    parts = [f"Температура {temp_str}", f"умови: {cond}", f"вітер {wind_str}", f"вологість {hum_str}"]
    if feels_str and feels != temp:
        parts.insert(1, f"відчувається {feels_str}")
    return ". ".join(parts) + "."
