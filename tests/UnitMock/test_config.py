"""Unit tests for config — env vars, no LLM."""

import pytest

from weather_agent.config import PROMPT_VERSION, DEFAULT_MODEL


@pytest.mark.unit_mock
class TestConfig:
    def test_prompt_version_is_string(self):
        assert isinstance(PROMPT_VERSION, str)
        assert PROMPT_VERSION in ("1", "2")

    def test_default_model_set(self):
        assert isinstance(DEFAULT_MODEL, str)
        assert len(DEFAULT_MODEL) > 0
