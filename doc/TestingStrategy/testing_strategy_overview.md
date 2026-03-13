```markdown name=testing_strategy_overview.md
# Testing Strategy Overview

## Purpose
This document provides a high-level summary of the testing strategy for the **Education Weather Agent** — a Telegram bot powered by LangChain that recommends what to wear based on real-time weather using OpenAI and Open-Meteo APIs.

**Audience**: Architects, engineering leads, managers, QA coordinators  
**Read Time**: 5-10 minutes  
**Next Steps**: See [Testing Layers Guide](testing_layers.md) for detailed specifications

---

## The Test Pyramid

The application follows a **6-layer test pyramid** organized by integration depth and execution scope:

```
                        🔴 SystemLLM (E2E + Real LLM)
                       /                          \
                      /    (Slow, Expensive,      \
                     /      Non-deterministic)     \
                    /________________________________\
                   /  🟠 IntegrationLLM (Real LLM)  \
                  /                                  \
                 /      (Slower, Moderately         \
                /        Expensive, Probabilistic)   \
               /____________________________________ \
              /  🟡 SystemMock (E2E + Fake LLM)     \
             /                                       \
            /       (Medium Speed, Free,             \
           /         Deterministic)                   \
          /______________________________________ \
         /  🟢 IntegrationMock (Fake + Mocked)     \
        /                                          \
       /      (Fast, Free, Deterministic)          \
      /______________________________ \
     /  🟢 UnitLLM (Fake LLM Unit)     \
    /                                   \
   /   (Fast, Free, Deterministic)      \
  /______________________________ \
 /  🟢 UnitMock (Pure Unit)        \
/_______________________________/
   (Fastest, Free, Deterministic)
```

**Key Principle**: Write **as many fast, cheap, deterministic tests as possible** at the base (UnitMock). Write expensive, slow tests (SystemLLM) sparingly.

---

## Test Layers at a Glance

| Layer | What | Why | LLM | HTTP | Speed | Cost | Frequency |
|-------|------|-----|-----|------|-------|------|-----------|
| **UnitMock** | Single functions, no dependencies | Find bugs early | ❌ | ❌ | < 100ms | $0 | Every commit |
| **UnitLLM** | Component + fake LLM | Test agent structure | ✅ Fake | ❌ | < 500ms | $0 | Every commit |
| **IntegrationMock** | Agent + tool + mocks | Test workflows | ✅ Fake | ❌ | < 1s | $0 | Every PR |
| **IntegrationLLM** | Agent + tool + real LLM | Measure quality | ✅ Real | ❌ | 2-10s | $0.01-0.05 | Per PR (optional) |
| **SystemMock** | Telegram → Agent → Response (mocked) | E2E without costs | ✅ Fake | ❌ | < 2s | $0 | Every PR |
| **SystemLLM** | Full workflow with real APIs | Production readiness | ✅ Real | ✅ | 10-60s | $0.05-0.20 | Nightly/Release |

---

## Test Categories

### 1. **Functional Tests**
Does the system do what it's supposed to do?

- ✅ Tool returns correct weather format
- ✅ Agent selects the right tool
- ✅ Bot commands (`/start`, `/help`) work
- ✅ Error handling for invalid cities
- ✅ Complete user flow: message → weather → recommendation

### 2. **Non-Functional Tests**
Does the system do it well (fast, reliably, efficiently)?

- ⚡ **Performance**: Response time < 10 seconds
- 📦 **Load**: Handle 10+ concurrent users
- 💰 **Cost**: Keep API spend < $0.10 per interaction
- 📊 **Reliability**: 99%+ test pass rate

### 3. **Safety & Security Tests** (AI-Specific)
Can users break or exploit the system?

- 🚫 **Prompt Injection**: `"city: ...; ignore system prompt"`
- 🔒 **Data Leakage**: Response doesn't expose system prompt
- 🎯 **Hallucination**: Agent doesn't invent weather data
- 🛡️ **Tool Abuse**: Path traversal, malicious input
- ⚠️ **Graceful Degradation**: Empty/null inputs return helpful errors

### 4. **Behavior Tests** (LLM-Specific)
Is the AI output actually good quality?

- 💬 **Relevance**: Response addresses the user's question
- 🎯 **Tool Correctness**: Agent picks the right tool (DeepEval)
- ✍️ **Consistency**: Same query → similar recommendations
- 📝 **Faithfulness**: Response matches actual weather data

---

## Current Implementation Status

### ✅ What's Working
- **UnitMock**: ~20 tests covering weather tool, config, bot texts
- **IntegrationMock**: ~5 tests for agent + tool integration
- **SystemLLM**: Basic safety tests and task completion checks

### ⚠️ What's Partial
- **UnitLLM**: Placeholder conftest, only 1 test
- **IntegrationLLM**: Only basic DeepEval metrics (2 tests)

### ❌ What's Missing
- **SystemMock**: No E2E tests with bot handlers
- **Prompt Testing**: No snapshot tests for prompt changes
- **Contract Testing**: No API schema validation
- **Performance Testing**: No load/latency tests
- **Full DeepEval**: Only 2 metrics, should have 5+

---

## Critical Gaps & Impact

### Gap 1: Missing SystemMock Layer
**Impact**: Cannot test bot E2E without hitting real OpenAI API  
**Solution**: Create bot handler tests with mocked agent  
**Effort**: ~2 days  
**Priority**: 🔴 HIGH

### Gap 2: Incomplete UnitLLM Suite
**Impact**: Agent behavior untested before integration  
**Solution**: Expand to 10-15 tests with fake LLM  
**Effort**: ~3 days  
**Priority**: 🔴 HIGH

### Gap 3: No Prompt Snapshot Tests
**Impact**: Prompt changes aren't validated, regressions missed  
**Solution**: Add `inline-snapshot` tests for prompt v1 and v2  
**Effort**: ~1 day  
**Priority**: 🟠 MEDIUM

### Gap 4: Sparse DeepEval Metrics
**Impact**: Output quality not comprehensively measured  
**Solution**: Implement 5+ metrics (Relevance, Hallucination, Faithfulness, etc.)  
**Effort**: ~3 days  
**Priority**: 🟠 MEDIUM

### Gap 5: Missing Contract Tests
**Impact**: Breaking changes in Open-Meteo/Telegram APIs not caught  
**Solution**: Add JSON Schema validation tests  
**Effort**: ~2 days  
**Priority**: 🟡 MEDIUM

### Gap 6: No Performance/Load Tests
**Impact**: Latency regressions and scalability issues missed  
**Solution**: Add response time benchmarks and concurrent user tests  
**Effort**: ~2 days  
**Priority**: 🟡 MEDIUM

---

## Key Metrics & KPIs

### Coverage
| Metric | Current | Target | Cadence |
|--------|---------|--------|---------|
| Test Coverage | ~40% | 80%+ | Every PR |
| UnitMock Tests | 20 | 50+ | Every commit |
| Integration Tests | 5 | 25+ | Every PR |
| Safety Tests | 3 | 10+ | Every release |

### Quality
| Metric | Target | Tracking |
|--------|--------|----------|
| Test Reliability | 99%+ | CI dashboard |
| Avg Response Time | < 10s | Weekly (SystemLLM) |
| Cost per Test | < $0.10 | Monthly audit |
| False Positive Rate | < 1% | Per test run |

---

## Test Markers (pytest)

All tests are tagged with markers for selective execution:

```bash
# Run only deterministic tests (no API calls)
pytest -m unit_mock

# Run all tests except expensive ones
pytest -m "not system_llm"

# Run only safety tests
pytest -m safety

# Run specific layer
pytest -m integration_mock
```

**Marker Hierarchy**:
```
unit_mock          → Single function, no LLM/HTTP
unit_llm           → Component + fake LLM
integration_mock   → Multi-component + mocks
integration_llm    → Multi-component + real LLM
system_mock        → E2E + fake LLM
system_llm         → E2E + real LLM
safety             → Security & injection tests
performance        → Load & latency tests
```

---

## Test Execution Guide

### Local Development
```bash
# Fast tests only (pre-commit)
make test-fast                    # UnitMock + UnitLLM (~5s)

# All deterministic tests (pre-PR)
make test-no-llm                  # + IntegrationMock + SystemMock (~30s)

# With quality metrics (if you have OPENAI_API_KEY)
make test-integration-llm         # IntegrationLLM (~2-3 min)

# Everything (rare, needs both API keys)
make test-all                     # + SystemLLM (~5-10 min)
```

### CI/CD Pipeline
```
Commit → UnitMock + UnitLLM (must pass)
   ↓
PR → + IntegrationMock + SystemMock (must pass)
   ↓
Merge to main → + IntegrationLLM (optional)
   ↓
Release tag → + SystemLLM + Performance (pre-release only)
```

---

## Architecture Overview

The application has 4 main layers:

```
┌─────────────────────────────────────────┐
│  Telegram Bot (python-telegram-bot)     │  ← Tests in SystemMock/SystemLLM
│  Handlers: /start, /help, messages      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  LangChain Agent (create_agent)         │  ← Tests in UnitLLM, IntegrationMock
│  Tool: get_weather                      │     IntegrationLLM, SystemLLM
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Weather Tool (Open-Meteo)              │  ← Tests in UnitMock
│  - Geocoding API (city → lat, lon)      │     IntegrationMock
│  - Forecast API (current weather)       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  External APIs                          │
│  - OpenAI (LLM)                         │
│  - Open-Meteo (Weather)                 │
│  - Telegram (Bot Platform)              │
└─────────────────────────────────────────┘
```

---

## Best Practices for LLM Agent Testing

### ✅ **DO**
1. **Test deterministically first** — start with UnitMock for all logic
2. **Mock external APIs** — don't call real services until necessary
3. **Use fake LLMs** — `GenericFakeChatModel` for testing message flow
4. **Measure quality** — DeepEval metrics for output evaluation
5. **Snapshot prompts** — catch regressions in system prompts
6. **Test contracts** — validate API schemas, not just happy paths
7. **Run safety tests** — prompt injection, data leakage, hallucinations
8. **Measure cost** — track $ per test for expensive LLM calls
9. **Use markers** — organize tests by complexity/cost with pytest markers
10. **Record fixtures** — VCR.py for deterministic HTTP replays

### ❌ **DON'T**
1. Don't test randomness directly — use statistical/property-based approaches
2. Don't call real APIs in unit tests — defeats the purpose of isolation
3. Don't ignore non-determinism — require high thresholds (0.7+) for probabilistic tests
4. Don't test the LLM — test your agent's behavior with the LLM
5. Don't skip safety tests — AI safety is critical
6. Don't hardcode API keys — always use environment variables/secrets
7. Don't mix layers — keep unit, integration, system tests separate
8. Don't forget edge cases — empty input, malformed data, network errors
9. Don't test without isolation — tests should be independent
10. Don't assume tests are cheap — expensive tests should be manual/nightly only

---

## Quick Links

| Document | Purpose | Audience |
|----------|---------|----------|
| [Testing Layers Guide](testing_layers.md) | Detailed specs for each layer | Developers, QA |
| [Testing Categories & Safety](testing_categories_and_safety.md) | Functional, non-functional, safety, behavior tests | QA, security engineers |
| [LLM Metrics & DeepEval](llm_metrics_and_deepeval.md) | How to measure output quality | AI specialists, QA |
| [Critical Gaps & Impact](#critical-gaps--impact) | Prioritized implementation roadmap | Managers, sprint planners |

---

## Questions?

- **How do I write a new test?** → See [Testing Layers Guide](testing_layers.md)
- **What's the difference between layers?** → See [Quick Comparison Table](#test-layers-at-a-glance) above
- **How do I test the LLM quality?** → See [LLM Metrics & DeepEval](llm_metrics_and_deepeval.md)
- **What should I prioritize?** → See [Critical Gaps & Impact](#critical-gaps--impact)

---

**Version**: 1.0  
**Last Updated**: 2026-03-13  
**Status**: Ready for Implementation
```
