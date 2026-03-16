# LLM Metrics & DeepEval

## Overview

This document provides comprehensive guidance on measuring LLM agent output quality using **DeepEval** — an open-source framework for evaluating LLM applications. It covers metric selection, setup, implementation, and best practices.

**Read Time**: 12-15 minutes  
**For**: AI specialists, QA engineers, test architects  

---

## Why DeepEval?

DeepEval solves the problem of testing non-deterministic LLM outputs:

- **LLM output varies**
    - Traditional testing: Can't assert exact match
    - DeepEval solution: Uses LLM-as-judge metrics
- **Quality is subjective**
    - Traditional testing: Hard to measure "good"
    - DeepEval solution: Provides 50+ metrics
- **No automated evaluation**
    - Traditional testing: Manual review required
    - DeepEval solution: Automated evaluation
- **Cost tracking**
    - Traditional testing: Manual logging
    - DeepEval solution: Built-in cost tracking
- **CI/CD integration**
    - Traditional testing: Custom setup
    - DeepEval solution: Native pytest integration

---

## DeepEval Architecture

1. **User query**
    - Example: "Що одягнути в Києві?"
2. **Agent execution (`ask_agent`)**
    - Uses `get_weather` + OpenAI LLM
3. **Test case construction (`LLMTestCase`)**
    - Includes `input`, `actual_output`, and optional expectations/context
4. **Metric evaluation (LLM-as-judge)**
    - Typical metrics: `AnswerRelevancyMetric`, `ToolCorrectnessMetric`, `HallucinationMetric`, `FaithfulnessMetric`
5. **Score output**
    - Numeric score in range `0.0-1.0`
    - Pass/fail depends on each metric threshold and semantics

---

## Core Metrics for Weather Agent

### 1. ToolCorrectnessMetric

**Question**: Did the agent use the correct tool?

**How it works**: LLM evaluator checks if `tools_called` matches `expected_tools`

For reliable results, capture `tools_called` from real traces/callbacks instead of hardcoding expected values.

**Use case**: Verify agent picks `get_weather` for weather queries

```python
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import ToolCorrectnessMetric
from deepeval import assert_test

@pytest.mark.integration_llm
def test_agent_uses_correct_tool():
    """Agent should call get_weather for weather questions."""
    
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
```

**Threshold guidance**:
- `0.5` — Lenient, allows some tool confusion
- `0.7` — Balanced (recommended)
- `0.9` — Strict, no tolerance for wrong tools

**Score interpretation**:
- ✅ `1.0` — Agent used exactly the right tool
- ⚠️ `0.5-0.9` — Agent used correct tool but with some issues
- ❌ `0.0` — Agent used wrong tool or no tool

---

### 2. AnswerRelevancyMetric

**Question**: Is the response relevant to the user's question?

**How it works**: LLM evaluator checks if `actual_output` addresses `input`

**Use case**: Verify response is about clothing, not random text

```python
from deepeval.metrics import AnswerRelevancyMetric

@pytest.mark.integration_llm
def test_answer_relevance():
    """Response must address the user's weather question."""
    
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

**Threshold guidance**:
- `0.5` — Lenient, answer just mentions weather
- `0.7` — Balanced (recommended)
- `0.9` — Strict, must directly answer question

**Score interpretation**:
- ✅ `1.0` — Response directly addresses query
- ⚠️ `0.5-0.9` — Response somewhat relevant but could be better
- ❌ `0.0` — Response completely off-topic

---

### 3. HallucinationMetric

**Question**: Did the agent invent facts not in the data?

**How it works**: Compares `actual_output` against `context` (ground truth)

**Use case**: Verify weather recommendations match actual weather data

```python
from deepeval.metrics import HallucinationMetric

@pytest.mark.integration_llm
def test_no_hallucination():
    """Agent should not invent weather data."""
    
    user_input = "Що одягнути в Києві?"
    actual_output = ask_agent(user_input)
    
    # Context is the actual weather data
    weather_context = [
        "Temperature: -2°C",
        "Conditions: Snow",
        "Wind: 15 km/h",
    ]
    
    test_case = LLMTestCase(
        input=user_input,
        actual_output=actual_output,
        context=weather_context,
    )
    
    assert_test(
        test_case,
        [HallucinationMetric(threshold=0.1)],  # Low threshold = strict
    )
```

**Threshold guidance**:
- `0.1` — Strict, no hallucination allowed (recommended)
- `0.3` — Moderate, some minor fabrication acceptable
- `0.5` — Lenient, significant hallucination allowed

**Score interpretation**:
- ✅ `0.0` — No hallucinations, all facts grounded
- ⚠️ `0.1-0.3` — Minor hallucinations detected
- ❌ `>0.3` — Significant hallucinations (agent invents facts)

---

### 4. FaithfulnessMetric

**Question**: Is the response faithful to the tool output?

**How it works**: Verifies `actual_output` aligns with `retrieval_context`

**Use case**: Verify recommendation matches actual weather

```python
from deepeval.metrics import FaithfulnessMetric

@pytest.mark.integration_llm
def test_faithfulness_to_weather_data():
    """Recommendation must be faithful to actual weather."""
    
    user_input = "Що одягнути в Львові?"
    actual_output = ask_agent(user_input)
    
    # This is the tool output (ground truth)
    weather_data = [
        "Current temperature: -5°C",
        "Weather: Light snow",
        "Wind speed: 12 km/h",
        "Humidity: 80%",
    ]
    
    test_case = LLMTestCase(
        input=user_input,
        actual_output=actual_output,
        retrieval_context=weather_data,
    )
    
    assert_test(
        test_case,
        [FaithfulnessMetric(threshold=0.7)],
    )
```

**Threshold guidance**:
- `0.5` — Lenient, some deviation acceptable
- `0.7` — Balanced (recommended)
- `0.9` — Strict, must closely follow context

**Score interpretation**:
- ✅ `0.9-1.0` — Response tightly follows context
- ⚠️ `0.5-0.8` — Response generally follows context
- ❌ `<0.5` — Response diverges from context

---

## Complete Example: Multi-Metric Test

```python
# tests/IntegrationLLM/test_deepeval_comprehensive.py

import os
import sys
from pathlib import Path
import pytest

from deepeval import assert_test
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import (
    ToolCorrectnessMetric,
    AnswerRelevancyMetric,
    HallucinationMetric,
    FaithfulnessMetric,
)

_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from weather_agent.agent import ask_agent

REQUIRES_OPENAI = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@pytest.mark.integration_llm
@REQUIRES_OPENAI
class TestComprehensiveQuality:
    """Test agent output quality with multiple metrics."""

    def test_kyiv_weather_all_metrics(self):
        """Test all metrics for Kyiv weather query."""
        
        user_input = "Що одягнути в Києві?"
        actual_output = ask_agent(user_input)
        
        # Context from get_weather tool output
        weather_context = [
            "Київ, Україна",
            "Температура: -2.5°C",
            "Відчувається як: -4.0°C",
            "Умови: Сніг слабкий",
            "Вітер: 15 км/год",
            "Вологість: 85%",
        ]
        
        test_case = LLMTestCase(
            input=user_input,
            actual_output=actual_output,
            context=weather_context,
            retrieval_context=weather_context,
            tools_called=[ToolCall(name="get_weather", args={"city": "Київ"})],
            expected_tools=[ToolCall(name="get_weather")],
        )
        
        # Run all metrics
        metrics = [
            ToolCorrectnessMetric(threshold=0.7, model="gpt-4o"),
            AnswerRelevancyMetric(threshold=0.7, model="gpt-4o"),
            HallucinationMetric(threshold=0.1, model="gpt-4o"),
            FaithfulnessMetric(threshold=0.7, model="gpt-4o"),
        ]
        
        assert_test(test_case, metrics)

    def test_lviv_weather_parametrized(self):
        """Test with different cities (could be parametrized)."""
        
        cities = ["Львів", "Одеса", "Харків"]
        
        for city in cities:
            user_input = f"Що одягнути в {city}?"
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

---

## Dataset-Based Testing (Parametrized)

Use **Golden** dataset format for testing multiple scenarios:

```python
# tests/IntegrationLLM/test_dataset_metrics.py

import pytest
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric
from weather_agent.agent import ask_agent

WEATHER_DATASET = EvaluationDataset(
    goldens=[
        Golden(input="Що одягнути в Києві?"),
        Golden(input="Як одягнутися сьогодні у Львові?"),
        Golden(input="Порадь, що вдягнути в Одесі"),
        Golden(input="Температура в Харкові - що одягнути?"),
        Golden(input="Погода в Запоріжжі - поради по одягу"),
    ]
)


@pytest.mark.integration_llm
@pytest.mark.parametrize("golden", WEATHER_DATASET.goldens)
def test_weather_relevance_dataset(golden):
    """Test answer relevance across multiple weather queries."""
    
    actual_output = ask_agent(golden.input)
    
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
    )
    
    assert_test(
        test_case,
        [AnswerRelevancyMetric(threshold=0.7)],
    )
```

**Run parametrized tests**:
```bash
# Run all dataset tests
pytest tests/IntegrationLLM/test_dataset_metrics.py -v

# Run with N parallel workers
pytest tests/IntegrationLLM/test_dataset_metrics.py -n 4

# Run with caching
deepeval test run tests/IntegrationLLM/test_dataset_metrics.py -c
```

---

## Setup & Configuration

### Installation

```bash
pip install deepeval
```

### Configuration in pyproject.toml

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "deepeval>=0.21",
    "ruff>=0.8.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration_llm: integration tests with real LLM",
    "system_llm: system tests with real APIs",
]
```

### Environment Setup

```bash
# Set OpenAI API key (required for DeepEval)
export OPENAI_API_KEY="sk-..."

# Optional: Set evaluator model (defaults to gpt-4o)
export DEEPEVAL_MODEL="gpt-4o"

# Optional: Confident AI API key (for cloud storage)
export CONFIDENT_API_KEY="..."
```

---

## Cost Management & Tracking

### Understanding Costs

Each metric call costs approximately:

- **ToolCorrectnessMetric**
    - Cost per test: `$0.002-0.005`
    - Notes: Simple LLM check
- **AnswerRelevancyMetric**
    - Cost per test: `$0.003-0.008`
    - Notes: Moderate reasoning
- **HallucinationMetric**
    - Cost per test: `$0.005-0.010`
    - Notes: Complex comparison
- **FaithfulnessMetric**
    - Cost per test: `$0.005-0.010`
    - Notes: Complex comparison
- **All 4 metrics combined**
    - Cost per test case: `$0.015-0.033`

**Example**: 10 test cases × 4 metrics × $0.020 = **$0.80 per test run**

### Cost Optimization

```python
# ❌ DON'T: Run all metrics for every test
assert_test(test_case, [
    ToolCorrectnessMetric(),
    AnswerRelevancyMetric(),
    HallucinationMetric(),
    FaithfulnessMetric(),
])  # Cost: $0.025 per test

# ✅ DO: Use strategic metric selection
# For quick checks: Only AnswerRelevancyMetric ($0.005)
# For releases: All 4 metrics ($0.025)

# Use markers to separate cost tiers
@pytest.mark.integration_llm
@pytest.mark.slow_expensive
def test_comprehensive():
    """Full metric suite (only before release)."""
    metrics = [
        ToolCorrectnessMetric(),
        AnswerRelevancyMetric(),
        HallucinationMetric(),
        FaithfulnessMetric(),
    ]
    assert_test(test_case, metrics)

@pytest.mark.integration_llm
def test_quick_relevance():
    """Quick relevance check (every PR)."""
    assert_test(test_case, [AnswerRelevancyMetric()])
```

### Cost Tracking Script

```python
# tests/cost_tracker.py

import os
from datetime import datetime

class CostTracker:
    """Track API costs for test runs."""
    
    METRIC_COSTS = {
        "ToolCorrectnessMetric": 0.003,
        "AnswerRelevancyMetric": 0.005,
        "HallucinationMetric": 0.007,
        "FaithfulnessMetric": 0.007,
    }
    
    def __init__(self, log_file="test_costs.log"):
        self.log_file = log_file
    
    def estimate_cost(self, num_tests, metrics):
        """Estimate total cost for a test run."""
        cost = 0
        for metric in metrics:
            metric_name = metric.__class__.__name__
            cost += self.METRIC_COSTS.get(metric_name, 0.005)
        
        total = cost * num_tests
        return total
    
    def log_cost(self, test_name, cost):
        """Log cost to file."""
        with open(self.log_file, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp} | {test_name} | ${cost:.4f}\n")

# Usage
tracker = CostTracker()
estimated = tracker.estimate_cost(num_tests=10, metrics=[
    ToolCorrectnessMetric(),
    AnswerRelevancyMetric(),
])
print(f"Estimated cost: ${estimated:.2f}")
```

---

## Testing Strategy by Layer

### UnitLLM Tests (Fake LLM, NO metrics needed)
```python
# No DeepEval needed - use GenericFakeChatModel
# Focus on message format, tool invocation structure
```

### IntegrationMock Tests (Fake LLM, NO metrics needed)
```python
# No DeepEval needed - mocked HTTP
# Focus on workflow, error handling
```

### IntegrationLLM Tests (Real LLM, metrics recommended)
```python
@pytest.mark.integration_llm
def test_with_deepeval():
    """Only use metrics for real LLM."""
    # Cost: $0.02-0.03 per test
    # Run: Every PR (optional) or nightly
```

### SystemLLM Tests (Real LLM, comprehensive metrics)
```python
@pytest.mark.system_llm
def test_with_full_metrics():
    """Full evaluation before release."""
    # Cost: $0.03 per test
    # Run: Pre-release, nightly, manual
```

---

## Pytest Integration

### Run DeepEval Tests

```bash
# Run all IntegrationLLM tests
pytest tests/IntegrationLLM/ -v

# Run only quick tests (single metric)
pytest tests/IntegrationLLM/ -m "not slow_expensive" -v

# Run with verbose output
pytest tests/IntegrationLLM/ -v --tb=short

# Run with cost tracking
pytest tests/IntegrationLLM/ -v -s  # -s for print statements
```

### CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Run DeepEval Tests
  if: github.event_name == 'pull_request'  # Only on PRs
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    pytest tests/IntegrationLLM/ -v -m "not slow_expensive"
    
- name: Run Full Metrics (Release)
  if: startsWith(github.ref, 'refs/tags/v')  # Only on release tags
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    pytest tests/IntegrationLLM/ tests/SystemLLM/ -v
```

---

## Common Issues & Solutions

### Issue 1: Test Hangs on Metric Evaluation

**Cause**: LLM evaluator taking too long  
**Solution**: Add timeout

```python
import pytest

@pytest.mark.integration_llm
@pytest.mark.timeout(30)  # 30 second timeout
def test_with_timeout():
    """Test with timeout."""
    assert_test(test_case, [AnswerRelevancyMetric()])
```

### Issue 2: Metric Score Always 0.0

**Cause**: Format mismatch in test case  
**Solution**: Verify test case structure

```python
# ❌ WRONG: Missing context
test_case = LLMTestCase(
    input="...",
    actual_output="...",
)  # HallucinationMetric needs context!

# ✅ CORRECT: Include context
test_case = LLMTestCase(
    input="...",
    actual_output="...",
    context=["weather data 1", "weather data 2"],
)
```

### Issue 3: High Cost in CI

**Cause**: Running expensive tests on every commit  
**Solution**: Use markers to skip in CI

```python
@pytest.mark.integration_llm
@pytest.mark.slow_expensive
def test_expensive():
    """Only run before release."""
    pass

# In CI: pytest -m "not slow_expensive"
```

### Issue 4: Flaky Tests (Inconsistent Scores)

**Cause**: LLM evaluator non-deterministic  
**Solution**: Run multiple times, average score, or increase threshold

```python
@pytest.mark.integration_llm
def test_with_retries():
    """Run test multiple times to reduce flakiness."""
    scores = []
    
    for _ in range(3):
        try:
            assert_test(test_case, [AnswerRelevancyMetric(threshold=0.6)])
            scores.append(1)
        except AssertionError:
            scores.append(0)
    
    # Pass if 2 out of 3 succeeded
    assert sum(scores) >= 2, f"Only {sum(scores)}/3 runs passed"
```

---

## Best Practices

### ✅ DO

1. **Use appropriate thresholds** — Not too strict (0.5) or too lenient (0.95)
2. **Test realistic queries** — Use real user scenarios, not edge cases
3. **Track costs** — Log metric expenses for budget management
4. **Combine metrics** — Use 2-4 metrics per test, not just one
5. **Run selectively** — Quality metrics on PRs, full suite pre-release
6. **Test different scenarios** — Cities, weather conditions, edge cases
7. **Document expected behavior** — What does "good" look like?
8. **Version your metrics** — Track metric version changes over time

### ❌ DON'T

1. Don't run DeepEval on every commit — Too expensive
2. Don't use extreme thresholds — 0.1 or 0.99 are unrealistic
3. Don't ignore LLM evaluation cost — Track and budget carefully
4. Don't skip context fields — Metrics need proper input
5. Don't test implementation details — Focus on user-facing behavior
6. Don't rely on single metric — Always use 2+ for validation
7. Don't ignore flakiness — LLM scores vary; design for it
8. Don't forget security metrics — HallucinationMetric is critical

---

## Summary: When to Use Each Metric

- **Weather query**
    - Recommended metrics: Relevance + ToolCorrectness
    - Thresholds: `0.7 + 0.7`
    - Approx. cost: `$0.008`
    - Typical run cadence: Every PR
- **Safety test**
    - Recommended metrics: Hallucination + Leakage
    - Thresholds: `0.1 + 0.0`
    - Approx. cost: `$0.007`
    - Typical run cadence: Pre-release
- **Quality audit**
    - Recommended metrics: All 4 metrics
    - Thresholds: `0.7 + 0.7 + 0.1 + 0.7`
    - Approx. cost: `$0.025`
    - Typical run cadence: Nightly
- **Regression test**
    - Recommended metrics: Relevance only
    - Threshold: `0.7`
    - Approx. cost: `$0.005`
    - Typical run cadence: Every commit

---

## Next Steps

- For **safety testing patterns**, see [Testing Categories & Safety](testing_categories_and_safety.md)
- For **layer specifications**, see [Testing Layers Guide](testing_layers.md)
- For **implementation priorities**, see [Testing Strategy Overview](testing_strategy_overview.md)

---

**Version**: 1.0  
**Last Updated**: 2026-03-13  
**Status**: Ready for Implementation
```
