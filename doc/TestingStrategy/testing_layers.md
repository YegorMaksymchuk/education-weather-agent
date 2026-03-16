# Testing Layers Guide

## Overview

This guide provides detailed specifications for each of the **6 test layers** in the pyramid. Each layer has a specific responsibility, execution speed, and cost profile.

**Read Time**: 15-20 minutes  
**For**: Developers, QA engineers, test maintainers  

---

## Quick Reference

- **Layer: UnitMock**
    - Scope: Single function
    - Components: `weather._weather_code_to_text()`
    - LLM: ❌
    - HTTP: ❌
    - Speed: `<100ms`
    - Cost: `$0`
    - When to run: Every commit
    - Example: `test_weather.py`
- **Layer: UnitLLM**
    - Scope: Component + fake LLM
    - Components: Agent message formatting
    - LLM: ✅ Fake
    - HTTP: ❌
    - Speed: `<500ms`
    - Cost: `$0`
    - When to run: Every commit
    - Example: `test_agent_fake_model.py`
- **Layer: IntegrationMock**
    - Scope: Multi-component + mocks
    - Components: Agent + tool + mocked HTTP
    - LLM: ✅ Fake
    - HTTP: ❌
    - Speed: `<1s`
    - Cost: `$0`
    - When to run: Pre-PR
    - Example: `test_agent_tool_flow.py`
- **Layer: IntegrationLLM**
    - Scope: Multi-component + real LLM
    - Components: Agent + tool + real OpenAI
    - LLM: ✅ Real
    - HTTP: ❌
    - Speed: `2-10s`
    - Cost: `$0.01-0.05`
    - When to run: Per PR (optional)
    - Example: `test_deepeval_metrics.py`
- **Layer: SystemMock**
    - Scope: E2E workflow + mocks
    - Components: Telegram → Bot → Agent (fake)
    - LLM: ✅ Fake
    - HTTP: ❌
    - Speed: `<2s`
    - Cost: `$0`
    - When to run: Pre-PR
    - Example: `test_bot_handlers.py`
- **Layer: SystemLLM**
    - Scope: Full E2E + real APIs
    - Components: Telegram → Bot → Agent (real)
    - LLM: ✅ Real
    - HTTP: ✅
    - Speed: `10-60s`
    - Cost: `$0.05-0.20`
    - When to run: Nightly/Release
    - Example: `test_safety.py`, `test_task_completion.py`

---

## Layer 1: UnitMock — Pure Unit Tests

### Purpose
Test **single components in isolation** with no external dependencies (no LLM, no HTTP).

### Characteristics
- ✅ **Deterministic**: Same input → always same output
- ✅ **Fast**: < 100ms per test
- ✅ **Free**: No API calls
- ✅ **Isolated**: No environmental dependencies
- ✅ **Easy to debug**: Simple failure messages

### What to Test
1. **Pure Functions** — math, string manipulation, parsing
   - `weather._weather_code_to_text(code)` — WMO code → Ukrainian text
   - Prompt template substitution
   - Config value validation

2. **Constants & Configuration**
   - `PROMPT_VERSION` environment variable
   - `DEFAULT_MODEL` defaults
   - `WELCOME_TEXT` and `HELP_TEXT` bot messages

3. **Tool Error Handling** (with mocked HTTP)
   - Empty city input → helpful error
   - Non-existent city → graceful message
   - Network timeout → error message (not exception)

4. **Data Structures**
   - API response parsing
   - Tool return type validation

### How to Mock HTTP
Use `unittest.mock.patch()` to replace `httpx.Client`:

```python
from unittest.mock import patch, MagicMock

@pytest.mark.unit_mock
def test_get_weather_with_mocked_http(mock_httpx_geocode_kyiv, mock_httpx_forecast):
    """Test get_weather with mocked HTTP responses."""
    
    def fake_get(url, params=None, **kwargs):
        r = MagicMock()
        r.raise_for_status = MagicMock()
        r.json.return_value = (
            mock_httpx_geocode_kyiv if "geocoding" in url 
            else mock_httpx_forecast
        )
        return r

    with patch("weather_agent.weather.httpx.Client") as mock_client_cls:
        client = MagicMock()
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        client.get = fake_get
        mock_client_cls.return_value = client

        out = get_weather("Kyiv")
        
        assert isinstance(out, str)
        assert "Температура" in out
        assert "°C" in out
```

### Real Examples from Repository

#### Example 1: WMO Code Mapping
```python
# tests/UnitMock/test_weather.py
@pytest.mark.unit_mock
class TestWeatherCodeToText:
    """Test WMO code to Ukrainian text mapping."""

    def test_clear_sky(self):
        assert _weather_code_to_text(0) == "ясно"

    def test_snow(self):
        assert _weather_code_to_text(71) == "сніг слабкий"
        assert _weather_code_to_text(75) == "сніг сильний"

    def test_rain(self):
        assert _weather_code_to_text(61) == "дощ слабкий"
        assert _weather_code_to_text(65) == "дощ сильний"

    def test_thunderstorm(self):
        assert _weather_code_to_text(95) == "гроза"
        assert _weather_code_to_text(99) == "гроза з сильним градом"

    def test_high_code_uses_largest_matching(self):
        # Code 100 is above all keys; maps to nearest lower (99)
        assert _weather_code_to_text(100) == "гроза з сильним градом"

    def test_negative_returns_unknown(self):
        assert _weather_code_to_text(-1) == "невідомо"
```

#### Example 2: Configuration
```python
# tests/UnitMock/test_config.py
@pytest.mark.unit_mock
class TestConfig:
    def test_prompt_version_is_string(self):
        assert isinstance(PROMPT_VERSION, str)
        assert PROMPT_VERSION in ("1", "2")

    def test_default_model_set(self):
        assert isinstance(DEFAULT_MODEL, str)
        assert len(DEFAULT_MODEL) > 0
```

#### Example 3: Bot Text Constants
```python
# tests/UnitMock/test_bot_texts.py
@pytest.mark.unit_mock
class TestBotTexts:
    def test_welcome_non_empty(self):
        assert isinstance(WELCOME_TEXT, str)
        assert len(WELCOME_TEXT.strip()) > 0

    def test_welcome_contains_example(self):
        assert "Києві" in WELCOME_TEXT or "одягнути" in WELCOME_TEXT

    def test_help_non_empty(self):
        assert isinstance(HELP_TEXT, str)
        assert len(HELP_TEXT.strip()) > 0

    def test_help_contains_commands(self):
        assert "/start" in HELP_TEXT
        assert "/help" in HELP_TEXT
```

### Running UnitMock Tests
```bash
# Run all UnitMock tests
pytest tests/UnitMock/ -v

# Run specific test class
pytest tests/UnitMock/test_weather.py::TestWeatherCodeToText -v

# With coverage
pytest tests/UnitMock/ --cov=src/weather_agent --cov-report=term-missing
```

### Pytest Marker
```python
@pytest.mark.unit_mock
```

### Current Status
- ✅ **~20 tests** covering weather tool, config, bot texts
- ⚠️ **Missing**: Prompt snapshot tests, advanced error cases

---

## Layer 2: UnitLLM — Unit Tests with Fake LLM

### Purpose
Test **agent behavior with an LLM** without calling the real OpenAI API. Uses LangChain's `GenericFakeChatModel` to simulate LLM responses.

### Characteristics
- ✅ **Deterministic**: Fake LLM returns scripted responses
- ✅ **Fast**: < 500ms per test
- ✅ **Free**: No API calls
- ✅ **Tests structure**: Message format, tool invocation, response parsing
- ❌ **Doesn't test**: LLM quality, reasoning, or intelligence

### What to Test
1. **Agent Message Formatting**
   - User input → properly formatted message for LLM
   - Prompt template substitution
   - Tool descriptions included

2. **Tool Invocation Logic**
   - Agent correctly calls `get_weather` tool
   - Tool parameters match schema
   - Multiple tool calls in sequence (if supported)

3. **Response Parsing**
   - LLM output → agent result → final response
   - Handling of different response formats (text, structured)
   - Error message propagation

4. **Agent Configuration**
   - System prompt loaded correctly
   - Tool properly registered
   - Model temperature/parameters respected

### How to Use Fake LLM

```python
from langchain_core.language_model.fake_llm import GenericFakeChatModel
from weather_agent.agent import create_agent
from weather_agent.weather import get_weather

@pytest.mark.unit_llm
def test_agent_with_fake_model():
    """Agent correctly orchestrates with fake LLM."""
    
    # Create fake LLM that returns scripted response
    fake_llm = GenericFakeChatModel(
        messages=[
            "I'll check the weather for Kyiv.",
            # (In real scenario, LLM would call tool here)
            "Based on the weather, wear a warm jacket.",
        ]
    )
    
    # Create agent with fake LLM
    agent = create_agent(
        fake_llm,
        tools=[get_weather],
        system_prompt="You help with weather recommendations.",
    )
    
    # Test agent behavior
    result = agent.invoke({
        "messages": [{"role": "user", "content": "What to wear in Kyiv?"}]
    })
    
    # Assert agent processed the request
    assert "messages" in result
    assert len(result["messages"]) > 0
```

### Real Example Structure
```python
# tests/UnitLLM/test_agent_fake_model.py (PLACEHOLDER - needs implementation)

@pytest.mark.unit_llm
class TestAgentWithFakeModel:
    """Agent behavior with GenericFakeChatModel."""
    
    def test_agent_invokes_tool(self, mock_httpx_for_weather):
        """Agent calls weather tool when asked about weather."""
        # Test implementation
        
    def test_agent_parses_tool_response(self, mock_httpx_for_weather):
        """Agent correctly formats tool output in response."""
        # Test implementation
        
    def test_agent_handles_empty_input(self):
        """Agent handles empty user input gracefully."""
        # Test implementation
```

### Pytest Marker
```python
@pytest.mark.unit_llm
```

### Current Status
- ⚠️ **Placeholder**: Only conftest.py exists
- ❌ **Missing**: 10-15 focused agent behavior tests

---

## Layer 3: IntegrationMock — Integration with Mocks

### Purpose
Test **multi-component workflows** (agent + tool) with mocked external dependencies. Verifies that components work together correctly without external API calls.

### Characteristics
- ✅ **Deterministic**: All HTTP/LLM responses mocked
- ✅ **Fast**: < 1 second per test
- ✅ **Free**: No API calls
- ✅ **Tests workflows**: Agent → Tool → Response flow
- ✅ **Tests contracts**: API request/response format

### What to Test
1. **Agent + Tool Integration**
   - User message → agent invokes tool → tool returns data → agent formats response
   - Tool return format matches agent expectations
   - Error handling in tool flow

2. **HTTP Contract Validation**
   - Tool request to Open-Meteo has correct format
   - Tool response parsing handles API JSON structure
   - Timeout/error scenarios handled gracefully

3. **Data Flow**
   - City name input → geocoding → coordinates
   - Coordinates → weather forecast → temperature/conditions
   - Weather data → Ukrainian formatted string

### How to Mock HTTP + Fake LLM

```python
from unittest.mock import MagicMock, patch
from weather_agent.agent import ask_agent
from weather_agent.weather import get_weather

@pytest.mark.integration_mock
class TestAgentToolIntegration:
    """Agent and tool together with mocked HTTP."""
    
    def test_agent_tool_integration(self, mock_httpx_geocode_kyiv, mock_httpx_forecast):
        """Agent calls tool and formats response correctly."""
        
        def fake_get(url, params=None, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            r.json.return_value = (
                mock_httpx_geocode_kyiv if "geocoding" in url 
                else mock_httpx_forecast
            )
            return r

        with patch("weather_agent.weather.httpx.Client") as mock_client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = fake_get
            mock_client_cls.return_value = client

            # Test tool contract
            out = get_weather.invoke({"city": "Kyiv"})
            
            assert isinstance(out, str)
            assert "Температура" in out
            assert "-2.5°C" in out or "°C" in out
```

### Real Example from Repository
```python
# tests/IntegrationMock/test_agent_tool_flow.py
@pytest.mark.integration_mock
class TestAgentToolIntegration:
    """Agent and tool together with mocked HTTP."""
    
    def test_tool_contract_returns_string(self, mock_httpx_geocode_kyiv, mock_httpx_forecast):
        """get_weather returns string for valid city with mocked HTTP."""

        def fake_get(url, params=None, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            r.json.return_value = (
                mock_httpx_geocode_kyiv if "geocoding" in url 
                else mock_httpx_forecast
            )
            return r

        with patch("weather_agent.weather.httpx.Client") as mock_client_cls:
            client = MagicMock()
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get = fake_get
            mock_client_cls.return_value = client

            out = get_weather.invoke({"city": "Lviv"})
            
        assert isinstance(out, str)
        assert len(out) > 0
```

### Shared Fixtures (conftest.py)
```python
# tests/conftest.py
@pytest.fixture
def mock_httpx_geocode_kyiv():
    """Fake geocoding response for Kyiv."""
    return {
        "results": [
            {
                "latitude": 50.45,
                "longitude": 30.52,
                "timezone": "Europe/Kyiv",
            }
        ]
    }


@pytest.fixture
def mock_httpx_forecast():
    """Fake forecast current weather."""
    return {
        "current": {
            "temperature_2m": -2.5,
            "apparent_temperature": -4.0,
            "weather_code": 71,
            "wind_speed_10m": 15.0,
            "relative_humidity_2m": 85,
        }
    }
```

### Pytest Marker
```python
@pytest.mark.integration_mock
```

### Current Status
- ⚠️ **Partial**: ~5 tests for agent + tool
- ❌ **Missing**: Bot + agent integration tests
- ❌ **Missing**: Error scenario tests

---

## Layer 4: IntegrationLLM — Integration with Real LLM

### Purpose
Test **agent output quality** using real OpenAI API and DeepEval metrics. Measures whether the agent produces relevant, accurate, hallucination-free responses.

### Characteristics
- ⏱️ **Slower**: 2-10 seconds per test
- 💰 **Expensive**: $0.01-0.05 per test
- ❌ **Non-deterministic**: LLM output varies
- ✅ **Tests quality**: Relevance, tool correctness, faithfulness
- ✅ **Tests intelligence**: Can agent reason about weather?

### What to Test
1. **Answer Relevance**
   - User query "What to wear in Kyiv?" → response is about clothing
   - Response directly addresses the question

2. **Tool Correctness**
   - Agent picks the right tool (`get_weather`)
   - Agent passes correct city name to tool
   - Agent doesn't invent tools

3. **Faithfulness**
   - Response matches actual weather data
   - No contradictions between data and recommendation

4. **Hallucination Detection**
   - Agent doesn't invent cities/temperatures
   - Agent doesn't make up weather codes

### How to Use DeepEval

```python
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import ToolCorrectnessMetric, AnswerRelevancyMetric

@pytest.mark.integration_llm
def test_agent_tool_correctness():
    """Verify agent selects and calls the correct tool."""
    user_input = "Як одягнутися сьогодні у Львові?"
    actual_output = ask_agent(user_input)
    
    test_case = LLMTestCase(
        input=user_input,
        actual_output=actual_output,
        tools_called=[ToolCall(name="get_weather")],
        expected_tools=[ToolCall(name="get_weather")],
    )
    
    assert_test(
        test_case,
        [ToolCorrectnessMetric(threshold=0.7)],
    )


@pytest.mark.integration_llm
def test_agent_answer_relevance():
    """Verify response is relevant to the user query."""
    user_input = "Що одягнути в Києві?"
    actual_output = ask_agent(user_input)
    
    test_case = LLMTestCase(
        input=user_input,
        actual_output=actual_output,
    )
    
    assert_test(
        test_case,
        [AnswerRelevancyMetric(threshold=0.7)],
    )
```

### Real Example from Repository
```python
# tests/IntegrationLLM/test_deepeval_metrics.py
@pytest.mark.integration_llm
@REQUIRES_OPENAI
class TestDeepevalMetrics:
    """Quality of agent output with DeepEval (needs real API)."""

    def test_tool_correctness_expects_get_weather(self):
        """Sanity check: ToolCorrectnessMetric runs with expected get_weather call."""
        user_input = "Як одягнутися сьогодні у Львові?"
        actual_output = ask_agent(user_input)
        
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
```

### Pytest Marker
```python
@pytest.mark.integration_llm
```

### Current Status
- ⚠️ **Minimal**: Only 2 basic metrics (ToolCorrectness, AnswerRelevancy)
- ❌ **Missing**: Hallucination, Faithfulness, Consistency tests

---

## Layer 5: SystemMock — E2E with Fake Agent

### Purpose
Test **end-to-end bot workflow** (Telegram → Bot → Agent → Response) with a mocked agent. Verifies bot handlers, message routing, and error handling without calling real LLM.

### Characteristics
- ✅ **Deterministic**: Agent output scripted
- ✅ **Fast**: < 2 seconds per test
- ✅ **Free**: No API calls
- ✅ **Tests E2E flow**: Message routing, handlers, async
- ✅ **Tests bot logic**: Commands, error messages

### What to Test
1. **Bot Commands**
   - `/start` → welcome message
   - `/help` → help text with examples
   - Unknown commands → handled gracefully

2. **Message Handling**
   - User sends text → bot calls agent
   - Agent response → sent back to user
   - Typing indicator shown
   - Errors handled gracefully

3. **Integration**
   - Message route: `Telegram → Update → Handler → Agent → Response`
   - Async handlers work correctly
   - Chat context preserved

### How to Mock Bot + Agent

```python
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update
import pytest

@pytest.mark.system_mock
@pytest.mark.asyncio
async def test_start_command():
    """User sends /start → bot replies with welcome message."""
    
    # Mock Telegram update
    update = MagicMock(spec=Update)
    update.message.text = "/start"
    update.effective_chat.id = 12345
    
    # Mock bot context
    context = AsyncMock()
    context.bot.send_message = AsyncMock()
    
    # Run handler
    from weather_agent.bot import start
    await start(update, context)
    
    # Verify bot sent message
    context.bot.send_message.assert_called()
    call_args = context.bot.send_message.call_args
    sent_text = call_args.kwargs['text']
    
    assert "Привіт" in sent_text or "одягнути" in sent_text


@pytest.mark.system_mock
@pytest.mark.asyncio
async def test_help_command():
    """User sends /help → bot replies with help text."""
    
    update = MagicMock(spec=Update)
    update.message.text = "/help"
    update.effective_chat.id = 12345
    
    context = AsyncMock()
    context.bot.send_message = AsyncMock()
    
    from weather_agent.bot import help_command
    await help_command(update, context)
    
    context.bot.send_message.assert_called()
    sent_text = context.bot.send_message.call_args.kwargs['text']
    
    assert "/start" in sent_text
    assert "/help" in sent_text
```

### Pytest Markers
```python
@pytest.mark.system_mock
@pytest.mark.asyncio
```

### Current Status
- ❌ **Missing**: Complete SystemMock layer not yet implemented
- **Needed**: 5-10 tests covering all bot handlers and error cases

---

## Layer 6: SystemLLM — Full E2E with Real APIs

### Purpose
Test the **complete application** with real OpenAI and Open-Meteo APIs. Verifies production readiness, safety, and task completion.

### Characteristics
- ⏱️ **Slow**: 10-60 seconds per test
- 💰 **Expensive**: $0.05-0.20 per test
- ❌ **Non-deterministic**: Real LLM, real weather data
- ✅ **Tests everything**: Full workflow, safety, performance
- ✅ **Pre-release quality**: Only run before releases

### What to Test
1. **Task Completion**
   - E2E: User message → weather recommendation
   - Agent successfully recommends clothing
   - Response is actionable

2. **Safety & Security**
   - Prompt injection attempts don't break system
   - System prompt not leaked in response
   - Invalid input handled gracefully
   - No stack traces shown to user

3. **Performance**
   - Response time < 10 seconds
   - Cost per interaction tracking

### Real Examples from Repository
```python
# tests/SystemLLM/test_task_completion.py
@pytest.mark.system_llm
@REQUIRES_OPENAI
class TestTaskCompletion:
    """Agent accomplishes the intended task end-to-end."""
    
    def test_weather_recommendation(self):
        """Agent provides clothing recommendation for a city."""
        response = ask_agent("Що одягнути в Києві?")
        
        assert len(response) > 0
        assert "Температура" in response or "рекомендую" in response.lower()


# tests/SystemLLM/test_safety.py
@pytest.mark.system_llm
@pytest.mark.safety
@REQUIRES_OPENAI
class TestSafety:
    """Safety behaviour: no prompt injection, no leakage, graceful misuse."""
    
    def test_data_leakage_no_system_prompt_in_output(self):
        """Response must not contain system prompt or internal instructions."""
        out = ask_agent("Що одягнути в Києві?")
        out_lower = out.lower()
        
        assert "system_prompt" not in out_lower
        assert "відповідай лише українською" not in out_lower

    def test_misuse_empty_input_returns_helpful_message(self):
        """Empty or invalid input returns user-facing error, no stack trace."""
        out = ask_agent("")
        
        assert "Traceback" not in out
        assert "Error" not in out or "Спробуйте" in out or "Напишіть" in out
        assert len(out) > 0
```

### Pytest Markers
```python
@pytest.mark.system_llm
@pytest.mark.safety
@pytest.mark.performance
```

### Current Status
- ⚠️ **Sparse**: Only basic safety and task completion checks
- ❌ **Missing**: Full safety test suite, performance benchmarks

---

## Fixture Setup (conftest.py)

### Shared Fixtures (tests/conftest.py)
```python
"""Shared pytest fixtures for weather agent tests."""

import sys
from pathlib import Path
import pytest

# Ensure src is on path
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def mock_httpx_geocode_kyiv():
    """Fake geocoding response for Kyiv."""
    return {
        "results": [
            {
                "latitude": 50.45,
                "longitude": 30.52,
                "timezone": "Europe/Kyiv",
            }
        ]
    }


@pytest.fixture
def mock_httpx_forecast():
    """Fake forecast current weather."""
    return {
        "current": {
            "temperature_2m": -2.5,
            "apparent_temperature": -4.0,
            "weather_code": 71,
            "wind_speed_10m": 15.0,
            "relative_humidity_2m": 85,
        }
    }


@pytest.fixture
def mock_httpx_empty_geocode():
    """Geocoding returns no results."""
    return {"results": []}


@pytest.fixture(autouse=True)
def env_isolate(monkeypatch):
    """Set safe defaults for optional vars."""
    monkeypatch.setenv("PROMPT_VERSION", "2")
    monkeypatch.setenv("DEFAULT_MODEL", "gpt-4o-mini")
```

### Layer-Specific Fixtures (e.g., tests/UnitLLM/conftest.py)
```python
"""Fixtures for UnitLLM: fake model, mocked HTTP for get_weather."""

@pytest.fixture
def mock_httpx_for_weather():
    """Mock httpx.Client for get_weather tests."""
    # Implementation specific to UnitLLM tests
```

---

## Running Tests by Layer

### Run Specific Layer
```bash
# UnitMock only
pytest tests/UnitMock/ -v

# UnitLLM only
pytest tests/UnitLLM/ -v

# All integration (Mock + LLM)
pytest tests/Integration*/ -v

# SystemMock only
pytest tests/SystemMock/ -v

# SystemLLM only (requires OPENAI_API_KEY)
pytest tests/SystemLLM/ -v
```

### Run by Marker
```bash
# All unit tests (no API calls)
pytest -m "unit_mock or unit_llm" -v

# All integration tests
pytest -m "integration_mock or integration_llm" -v

# All system tests
pytest -m "system_mock or system_llm" -v

# Only safety tests
pytest -m safety -v

# Everything except slow SystemLLM
pytest -m "not system_llm" -v
```

### Run by Speed
```bash
# Fast tests (UnitMock + UnitLLM)
pytest tests/UnitMock tests/UnitLLM -v

# Medium speed (+ IntegrationMock + SystemMock)
pytest tests/UnitMock tests/UnitLLM tests/IntegrationMock tests/SystemMock -v

# All tests
pytest tests/ -v
```

---

## Best Practices per Layer

### UnitMock Best Practices
- ✅ Keep tests < 100ms each
- ✅ Use fixtures for reusable mock data
- ✅ Mock at the right level (function vs class)
- ✅ Test edge cases (empty input, None, negative, etc.)
- ❌ Don't test implementation details
- ❌ Don't make external calls

### UnitLLM Best Practices
- ✅ Use `GenericFakeChatModel` for LLM
- ✅ Mock HTTP for tool calls
- ✅ Test message formatting and parsing
- ✅ Keep responses deterministic
- ❌ Don't test LLM intelligence
- ❌ Don't rely on real model behavior

### IntegrationMock Best Practices
- ✅ Test realistic workflows
- ✅ Use shared fixtures (conftest.py)
- ✅ Test error scenarios
- ✅ Keep < 1 second per test
- ❌ Don't call real APIs
- ❌ Don't test all variations (that's unit tests)

### IntegrationLLM Best Practices
- ✅ Use DeepEval metrics for quality
- ✅ Set appropriate thresholds (0.5-0.9)
- ✅ Test with actual user queries
- ✅ Track API costs
- ✅ Run per-PR or nightly (not every commit)
- ❌ Don't test low-value quality attributes
- ❌ Don't expect deterministic results

### SystemMock Best Practices
- ✅ Test all bot handlers
- ✅ Test async message flow
- ✅ Mock agent responses
- ✅ Test error paths
- ❌ Don't use real agent/LLM
- ❌ Don't test network code

### SystemLLM Best Practices
- ✅ Test critical paths only
- ✅ Include safety/security tests
- ✅ Monitor API costs
- ✅ Run before release/nightly
- ✅ Use high thresholds for metrics
- ❌ Don't run on every commit
- ❌ Don't test all variations

---

## Troubleshooting

### Test Hangs or Timeouts
- **UnitMock**: Check for infinite loops in mocks
- **IntegrationLLM**: LLM API may be slow; increase timeout
- **SystemLLM**: Network call may be slow; set 30s timeout

### Test Flakiness
- **UnitLLM/IntegrationLLM**: LLM randomness; increase threshold or repeat
- **SystemLLM**: Weather data changes; use fixed test cities
- **All**: Check for race conditions in async tests

### Mocking Not Working
- **Wrong module path**: `patch("weather_agent.weather.httpx")` not `patch("httpx")`
- **Too late**: Patch before import, not after
- **Wrong object**: Mock the client, not the module

---

## Next Steps

- For **safety tests**, see [Testing Categories & Safety](testing_categories_and_safety.md)
- For **quality metrics**, see [LLM Metrics & DeepEval](llm_metrics_and_deepeval.md)
- For **implementation priorities**, see [Testing Strategy Overview](testing_strategy_overview.md)

---

**Version**: 1.0  
**Last Updated**: 2026-03-13  
**Status**: Ready for Development
```
