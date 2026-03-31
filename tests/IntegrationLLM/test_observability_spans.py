"""Integration tests: `ask_agent` OpenTelemetry spans for Grafana (exceptions, LLM traffic).

Happy-path test needs a real OpenAI key. Error-path uses a stub agent (no API calls).
With `OTEL_TESTS_EXPORT=1` and `make observability-up`, traces appear in ClickHouse/Grafana.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import weather_agent.agent as agent_mod

REQUIRES_OPENAI = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@pytest.fixture
def reset_cached_agent():
    """Avoid stale LangGraph agent between tests."""
    prev = agent_mod._agent
    agent_mod._agent = None
    yield
    agent_mod._agent = prev


@pytest.mark.integration_llm
@REQUIRES_OPENAI
def test_ask_agent_happy_path_emits_llm_stack(reset_cached_agent):
    """Real LLM + tools: OpenLIT emits chat / workflow / execute_tool spans when OTLP is enabled."""
    out = agent_mod.ask_agent("Що одягнути в Києві?")
    assert len(out.strip()) > 0
    assert "Traceback" not in out


@pytest.mark.integration_llm
def test_ask_agent_records_exception_on_invoke_failure(monkeypatch, reset_cached_agent):
    """Invoke failure: span records exception (Grafana «Last Exceptions» when exported)."""

    class _BadAgent:
        def invoke(self, *args, **kwargs):
            raise RuntimeError("simulated agent failure")

    monkeypatch.setattr(agent_mod, "_get_agent", lambda: _BadAgent())
    out = agent_mod.ask_agent("Що одягнути в Києві?")
    assert "simulated agent failure" in out
    assert "помилка" in out.lower() or "Помилка" in out
