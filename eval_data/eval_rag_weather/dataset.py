"""
Eval dataset for RAGAS: weather agent RAG (question, contexts, answer, ground_truth).
"""

from __future__ import annotations

from pathlib import Path

try:
    from datasets import Dataset
except ImportError:
    Dataset = None  # type: ignore[misc, assignment]


def get_eval_dataset() -> "Dataset":
    """Returns a small HF Dataset for RAGAS evaluation (weather + optional historical)."""
    if Dataset is None:
        raise ImportError("Install datasets: pip install datasets")
    data = {
        "question": [
            "Що одягнути сьогодні в Києві?",
            "Як одягнутися у Львові зараз?",
        ],
        "contexts": [
            [
                "2 березня 1985, Київ: температура макс 8.2°C, мін -1.1°C, опади 0 мм, сніг 0 мм.",
                "2 березня 2000, Київ: температура макс 5.0°C, мін -3.0°C, опади 0 мм.",
            ],
            [
                "2 березня 1990, Львів: макс 4.0°C, мін -2.0°C, опади 2.0 мм.",
            ],
        ],
        "answer": [
            "Температура в Києві зараз +6°C, умови ясно. Рекомендую легку куртку та взуття по погоді. "
            "Такий день в історії часто бував помірно холодним — сьогодні трохи тепліше. Гарного дня!",
            "У Львові зараз +3°C, хмарно. Варто вдягнути теплішу куртку та шарф. "
            "Історично в цей день бувало подібно. Бережіть себе!",
        ],
        "ground_truth": [
            "Рекомендація по одягу для Києва з урахуванням поточної погоди; опційно порівняння з історичною погодою.",
            "Рекомендація по одягу для Львова; порада щодо погоди українською.",
        ],
    }
    return Dataset.from_dict(data)


def get_eval_dataset_path() -> Path:
    """Directory of this dataset."""
    return Path(__file__).resolve().parent


__all__ = ["get_eval_dataset", "get_eval_dataset_path"]
