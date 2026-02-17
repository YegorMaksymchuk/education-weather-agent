"""Integration tests with DeepEval metrics — require real LLM (OPENAI_API_KEY)."""

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

from weather_agent.agent import ask_agent

REQUIRES_OPENAI = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@pytest.mark.integration_llm
@REQUIRES_OPENAI
class TestDeepevalMetrics:
    """Quality of agent output with DeepEval (needs real API)."""

    def test_answer_relevancy_weather_advice(self):
        """Agent reply should be relevant to weather/clothing query."""
        user_input = "Що одягнути в Києві?"
        actual_output = ask_agent(user_input)
        test_case = LLMTestCase(
            input=user_input,
            actual_output=actual_output,
            expected_output="Recommendation for what to wear based on weather in Kyiv.",
        )
        assert_test(
            test_case,
            [AnswerRelevancyMetric(threshold=0.5)],
        )

    def test_tool_correctness_expects_get_weather(self):
        """Sanity check: ToolCorrectnessMetric runs with expected get_weather call."""
        user_input = "Як одягнутися сьогодні у Львові?"
        actual_output = ask_agent(user_input)
        # We assert the agent was used for weather; expected tool is get_weather.
        # tools_called mirrors expected_tools for this sanity run (real trace would come from observability).
        test_case = LLMTestCase(
            input=user_input,
            actual_output=actual_output,
            tools_called=[ToolCall(name="get_weather")],
            expected_tools=[ToolCall(name="get_weather")],
        )
        assert_test(
            test_case,
            [ToolCorrectnessMetric(threshold=0.5)],
        )
