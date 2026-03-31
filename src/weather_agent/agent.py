"""LangChain-агент з tool погоди та обгортка для бота."""

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from weather_agent.config import DEFAULT_MODEL, require_openai_key
from weather_agent.prompts import get_system_prompt
from weather_agent.weather import get_weather
from weather_agent.historical.tools import get_historical_weather
from weather_agent.calendar.google_toolkit import get_calendar_tools_for_agent

_agent = None

_tracer = trace.get_tracer(__name__)


def _get_agent():
    """Лінива ініціалізація агента (потрібен OPENAI_API_KEY)."""
    global _agent
    if _agent is None:
        require_openai_key()
        model = ChatOpenAI(model=DEFAULT_MODEL, temperature=0)
        calendar_tools = get_calendar_tools_for_agent()
        _agent = create_agent(
            model,
            tools=[get_weather, get_historical_weather, *calendar_tools],
            system_prompt=get_system_prompt(),
        )
    return _agent


def ask_agent(user_text: str) -> str:
    """
    Відправляє запит користувача агенту й повертає текст відповіді.
    При помилці повертає повідомлення про збій українською.
    """
    if not user_text or not user_text.strip():
        return "Напишіть, для якого міста потрібна порада (наприклад: Що одягнути в Києві?)."

    stripped = user_text.strip()
    with _tracer.start_as_current_span(
        "ask_agent",
        attributes={
            "gen_ai.operation.name": "agent_request",
            "gen_ai.input.user_text": stripped[:500],
        },
    ) as span:
        try:
            agent = _get_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": stripped}]})
            messages = result.get("messages") or []
            if not messages:
                return "Не вдалося отримати відповідь. Спробуйте ще раз."

            last = messages[-1]
            content = getattr(last, "content", None) or (
                last.get("content") if isinstance(last, dict) else None
            )
            if isinstance(content, list):
                # Деякі моделі повертають content як список частин
                text_parts = [p.get("text", p) if isinstance(p, dict) else str(p) for p in content]
                content = "".join(str(t) for t in text_parts)
            if content:
                return content.strip()
            return "Відповідь порожня. Спробуйте переформулювати запит."
        except SystemExit:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return f"Виникла помилка: {e!s}. Спробуйте пізніше."
