"""System tests: E2E task completion with real agent — require OPENAI_API_KEY."""

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

REQUIRES_OPENAI = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@pytest.mark.system_llm
@REQUIRES_OPENAI
class TestTaskCompletion:
    """Agent accomplishes the intended task end-to-end."""

    def test_weather_advice_returns_non_empty_relevant_reply(self):
        """For a weather query, agent returns a non-empty reply about clothing/weather."""
        from weather_agent.agent import ask_agent

        out = ask_agent("Порадь, що одягнути в Києві.")
        assert isinstance(out, str)
        assert len(out.strip()) > 0
        # Should mention clothing or weather-related terms (Ukrainian)
        out_lower = out.lower()
        assert any(
            w in out_lower
            for w in ["одяг", "куртк", "шапк", "погод", "температур", "тепл", "холод"]
        )
