"""LLM-as-judge regression test: run judge on alignment dataset, check alignment rate."""

import asyncio
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
@pytest.mark.asyncio
async def test_llm_judge_alignment_regression():
    """Run historical_advice_quality judge on alignment dataset; assert alignment >= 0.5."""
    from openai import AsyncOpenAI

    from eval_data.eval_rag_weather.judge_alignment_dataset import get_judge_alignment_dataset
    from ragas.llms import llm_factory
    from weather_agent.eval.judge_metrics import get_historical_advice_quality_metric

    dataset = get_judge_alignment_dataset()
    metric = get_historical_advice_quality_metric()
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    llm = llm_factory("gpt-4o-mini", client=client)

    passed = 0
    total = len(dataset)
    for i in range(total):
        row = dataset[i]
        result = await metric.ascore(
            question=row["question"],
            grading_notes=row["grading_notes"],
            response=row["response"],
            llm=llm,
        )
        judge_label = (result.value or "").strip().lower() if hasattr(result, "value") else ""
        human_label = (row["target"] or "").strip().lower()
        if judge_label == human_label:
            passed += 1

    alignment_rate = passed / total if total else 0.0
    assert alignment_rate >= 0.5, f"Judge alignment {passed}/{total} = {alignment_rate:.2f} below 0.5"

# TODO
# To add example how to test too many content in answer of AI-agent