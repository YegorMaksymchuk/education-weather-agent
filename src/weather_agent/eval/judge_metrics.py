"""
LLM-as-judge metric for weather agent: порада по одягу та історичне порівняння.
"""

from __future__ import annotations

from ragas.metrics import DiscreteMetric

HISTORICAL_ADVICE_QUALITY_PROMPT_UA = """Оціни відповідь помічника про погоду та одяг.

Питання: {question}
Вимоги (grading_notes): {grading_notes}
Відповідь: {response}

Чи відповідає відповідь вимогам? Враховуй: наявність поради по одягу, згадку погоди, за бажанням — порівняння з історичною погодою. Приймай семантичні відповіді (не вимагай точних слів). Поверни тільки 'pass' або 'fail'."""


def get_historical_advice_quality_metric() -> DiscreteMetric:
    """Повертає DiscreteMetric для оцінки якості поради (одяг + опційно історія)."""
    return DiscreteMetric(
        name="historical_advice_quality",
        prompt=HISTORICAL_ADVICE_QUALITY_PROMPT_UA,
        allowed_values=["pass", "fail"],
    )
