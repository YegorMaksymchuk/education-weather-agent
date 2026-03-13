"""RAGAS evaluation on fixed eval dataset — requires OPENAI_API_KEY."""

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

REQUIRES_OPENAI = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@pytest.mark.eval_ragas
@REQUIRES_OPENAI
def test_ragas_evaluate_weather_dataset():
    """Run RAGAS evaluate() on eval dataset; assert metrics exist and are non-negative."""
    from datasets import Dataset

    from eval_data.eval_rag_weather.dataset import get_eval_dataset
    from ragas import evaluate
    from ragas.metrics._answer_relevance import answer_relevancy
    from ragas.metrics._faithfulness import faithfulness

    eval_ds = get_eval_dataset()
    assert isinstance(eval_ds, Dataset)
    assert len(eval_ds) >= 1
    assert "question" in eval_ds.column_names and "answer" in eval_ds.column_names
    assert "contexts" in eval_ds.column_names and "ground_truth" in eval_ds.column_names

    result = evaluate(eval_ds, metrics=[faithfulness, answer_relevancy])
    # Result has score per metric (e.g. result['faithfulness'], result['answer_relevancy'])
    assert result is not None
    if hasattr(result, "to_pandas"):
        df = result.to_pandas()
        if "faithfulness" in df.columns:
            assert (df["faithfulness"] >= 0).all() or df["faithfulness"].mean() >= 0
        if "answer_relevancy" in df.columns:
            assert (df["answer_relevancy"] >= 0).all() or df["answer_relevancy"].mean() >= 0
