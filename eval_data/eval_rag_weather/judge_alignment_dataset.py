"""
Alignment dataset for LLM-as-judge: question, response, grading_notes, target (pass/fail).
Used to align the judge with human expert labels and run regression tests.
"""

from __future__ import annotations

from pathlib import Path

try:
    from datasets import Dataset
except ImportError:
    Dataset = None  # type: ignore[misc, assignment]


def get_judge_alignment_dataset() -> "Dataset":
    """Returns a small dataset for judge alignment: grading_notes + human target (pass/fail)."""
    if Dataset is None:
        raise ImportError("Install datasets: pip install datasets")
    data = {
        "question": [
            "Що одягнути сьогодні в Києві?",
            "Як одягнутися у Львові?",
        ],
        "response": [
            "Температура в Києві +6°C, ясно. Рекомендую легку куртку. "
            "У минулі роки в цей день було подібно — помірно холодно. Гарного дня!",
            "У Львові зараз холодно. Одягніться тепліше.",
        ],
        "grading_notes": [
            "Порада по одягу для Києва; згадка поточної погоди; опційно історичне порівняння.",
            "Порада по одягу для Львова; коротка рекомендація.",
        ],
        "target": ["pass", "pass"],
    }
    return Dataset.from_dict(data)


__all__ = ["get_judge_alignment_dataset"]
