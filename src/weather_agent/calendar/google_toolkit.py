"""Адаптер для LangChain Google Calendar Toolkit.

Використовує офіційний CalendarToolkit з пакета
`langchain-google-community[calendar]` і повертає список tools,
які можна підключити до агента.

Документація: https://docs.langchain.com/oss/python/integrations/tools/google_calendar
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, List

from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import (
    build_calendar_service,
    get_google_credentials,
)

from weather_agent.config import (
    GOOGLE_CALENDAR_CREDENTIALS_PATH,
    GOOGLE_CALENDAR_TOKEN_PATH,
)


@lru_cache(maxsize=1)
def _build_calendar_toolkit() -> CalendarToolkit:
    """Створює інстанс CalendarToolkit з урахуванням налаштувань credentials.

    Якщо явно вказані шляхи до credentials/token, використовує їх.
    Інакше покладається на стандартну поведінку CalendarToolkit (пошук
    локального `credentials.json` тощо), як у офіційній документації.
    """
    if GOOGLE_CALENDAR_CREDENTIALS_PATH:
        # Використовуємо розширений шлях ініціалізації з прикладу у доках:
        # https://docs.langchain.com/oss/python/integrations/tools/google_calendar
        creds = get_google_credentials(
            token_file=GOOGLE_CALENDAR_TOKEN_PATH or "token.json",
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
            client_secrets_file=GOOGLE_CALENDAR_CREDENTIALS_PATH,
        )
        api_resource = build_calendar_service(credentials=creds)
        return CalendarToolkit(api_resource=api_resource)

    # Fallback на дефолтний конструктор (шукає credentials.json самостійно)
    return CalendarToolkit()


def get_calendar_tools_for_agent() -> List[Any]:
    """Повертає список tools для підключення до агента.

    Зараз повертаємо всі tools з CalendarToolkit, але за потреби можна
    відфільтрувати до підмножини (наприклад, лише пошук/читання подій).
    """
    toolkit = _build_calendar_toolkit()
    tools = list(toolkit.get_tools())
    return tools
