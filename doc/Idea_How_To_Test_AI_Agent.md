ыі# Testing AI agents: unit, integration, and system testing with DeepEval

**The testing landscape for AI agents has fundamentally changed.** Traditional software testing assumes deterministic input-output relationships, but AI agents introduce probabilistic behavior, tool orchestration, and multi-turn reasoning that demand entirely new approaches. This guide provides a comprehensive framework for Automation Test Engineering lectures, covering every layer of the AI agent testing pyramid — from isolated component unit tests through complex system-level evaluations — with practical DeepEval code examples throughout. The core insight driving modern AI agent testing: organize your test strategy by **uncertainty tolerance**, not just test granularity, with deterministic tests at the base and probabilistic evaluation at the top.

---

## 1. Unit testing individual AI agent components

Unit testing AI agent components requires isolating each piece — LLM calls, tools, prompts, parsers, and memory — from the rest of the system. The fundamental challenge is that LLM calls are non-deterministic, so the primary strategy is **mocking LLM responses to create deterministic unit tests** while reserving real LLM calls for integration and evaluation tests.

### Mocking LLM calls with unittest.mock

The most common pattern wraps the OpenAI client with `unittest.mock.patch`:

```python
import pytest
from unittest.mock import patch, MagicMock
from my_agent.chat_service import ChatService

class TestChatService:
    @patch('openai.OpenAI')
    def test_successful_chat_completion(self, mock_openai):
        # Arrange: build mock response matching OpenAI's structure
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Paris is the capital of France."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = ChatService("test-key")
        result = service.get_response("What is the capital of France?")

        assert result == "Paris is the capital of France."
        mock_client.chat.completions.create.assert_called_once()

    @patch('openai.OpenAI')
    def test_handles_api_error(self, mock_openai):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Rate limit")
        mock_openai.return_value = mock_client

        service = ChatService("test-key")
        with pytest.raises(Exception, match="Rate limit"):
            service.get_response("Any prompt")
```

LangChain provides `GenericFakeChatModel` for framework-native mocking, which returns predetermined responses including tool calls:

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolCall

model = GenericFakeChatModel(messages=iter([
    AIMessage(content="", tool_calls=[
        ToolCall(name="get_weather", args={"city": "SF"}, id="call_1")
    ]),
    "The weather in SF is sunny and 72°F."
]))

result = model.invoke("What's the weather?")  # Returns tool call
result2 = model.invoke("Thanks!")              # Returns text
```

PydanticAI offers an even cleaner approach with `TestModel` and a global safety switch that **prevents accidental real API calls** in test suites:

```python
from pydantic_ai import models
from pydantic_ai.models.test import TestModel

models.ALLOW_MODEL_REQUESTS = False  # Block all real API calls globally

@pytest.fixture
def override_agent():
    with weather_agent.override(model=TestModel()):
        yield

async def test_forecast(override_agent):
    result = await run_weather_forecast("London")
    assert result is not None
```

### Testing tool and function calling logic in isolation

Tools should be tested as pure functions, completely independent of the LLM:

```python
import pytest
from unittest.mock import MagicMock

def test_search_database_returns_ranked_results():
    """Test tool function in complete isolation from LLM."""
    mock_db = MagicMock()
    mock_db.query.return_value = [
        {"id": 1, "title": "Result 1", "score": 0.95},
        {"id": 2, "title": "Result 2", "score": 0.87},
    ]
    results = search_database("test query", db_client=mock_db)
    assert len(results) == 2
    assert results[0]["score"] > results[1]["score"]
    mock_db.query.assert_called_once_with("test query")

def test_search_database_handles_empty_results():
    mock_db = MagicMock()
    mock_db.query.return_value = []
    results = search_database("nonexistent", db_client=mock_db)
    assert results == []

def test_search_database_propagates_connection_error():
    mock_db = MagicMock()
    mock_db.query.side_effect = ConnectionError("DB unavailable")
    with pytest.raises(ConnectionError):
        search_database("query", db_client=mock_db)
```

The testing pyramid for tools has **three mocking levels**: (1) mock the tool itself to test agent reasoning and tool selection, (2) mock HTTP/DB calls within tools to test tool implementation, and (3) use dependency injection for full swappability.

### Testing prompt templates

Prompt templates should be tested for correct variable substitution, structural integrity, and regression:

```python
from langchain_core.prompts import ChatPromptTemplate

def test_prompt_template_substitution():
    template = ChatPromptTemplate.from_messages([
        ("system", "You are a {role} specialized in {domain}."),
        ("human", "{user_input}"),
    ])
    messages = template.format_messages(
        role="data analyst", domain="finance", user_input="Explain P/E ratio"
    )
    assert messages[0].content == "You are a data analyst specialized in finance."
    assert messages[1].content == "Explain P/E ratio"

def test_prompt_includes_required_instructions():
    prompt = build_system_prompt(context="medical", safety_level="high")
    assert "not a medical professional" in prompt.lower()
    assert "consult a doctor" in prompt.lower()
```

For **snapshot testing**, the `inline-snapshot` library automatically captures and compares prompt outputs across test runs, catching unintended prompt regressions:

```python
from inline_snapshot import snapshot

def test_prompt_renders_correctly():
    prompt = build_system_prompt(context="financial", user_level="expert")
    assert prompt == snapshot("""\
You are an expert financial advisor. Provide detailed analysis
with technical terminology appropriate for experienced investors.""")
```

### Testing parsers and output formatters

```python
def test_json_parser_handles_valid_output():
    parser = JsonOutputParser()
    result = parser.parse('{"name": "Alice", "skills": ["Python", "ML"]}')
    assert result["name"] == "Alice"
    assert "Python" in result["skills"]

def test_json_parser_rejects_invalid_output():
    parser = JsonOutputParser()
    with pytest.raises(Exception):
        parser.parse("This is not JSON")

def test_output_always_has_required_fields():
    """Property-based test: every output must contain status field."""
    test_outputs = ["The answer is 42", '{"result": "ok"}', "Error occurred", ""]
    for output in test_outputs:
        result = MyStructuredParser().parse(output)
        assert "status" in result
        assert isinstance(result["status"], str)
```

### Testing memory modules

```python
def test_context_window_truncation():
    memory = ConversationBufferWindowMemory(k=3)
    for i in range(5):
        memory.save_context({"input": f"Q{i}"}, {"output": f"A{i}"})
    history = memory.load_memory_variables({})
    assert "Q4" in str(history)     # Recent messages kept
    assert "Q0" not in str(history)  # Old messages dropped

def test_memory_persistence_across_turns():
    model = GenericFakeChatModel(messages=iter([
        AIMessage(content="Got it, you're in Sydney!"),
        AIMessage(content="It's currently around 10 PM AEST."),
    ]))
    agent = create_agent(model, tools=[], checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "session-1"}}
    
    agent.invoke({"messages": [HumanMessage("I live in Sydney")]}, config=config)
    result = agent.invoke({"messages": [HumanMessage("What's my time?")]}, config=config)
    assert "Sydney" in result["messages"][-1].content or "AEST" in result["messages"][-1].content
```

### Handling non-determinism in unit tests

Even at **temperature=0**, LLMs are non-deterministic — research shows accuracy variations up to **15%** across identical runs due to floating-point non-associativity in GPU computations and sparse mixture-of-experts routing. Four strategies address this:

**Strategy 1 — Mocking (preferred for CI):** Replace LLM calls with predetermined responses. Fast, free, deterministic.

**Strategy 2 — Semantic similarity assertions:** For tests that must use real LLM calls, compare meaning rather than exact strings:

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def assert_semantically_similar(response, expected, threshold=0.85):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    similarity = cosine_similarity(
        model.encode([response]), model.encode([expected])
    )[0][0]
    assert similarity >= threshold, f"Similarity {similarity:.3f} < {threshold}"
```

**Strategy 3 — Property-based testing:** Assert structural invariants that always hold regardless of specific wording:

```python
def test_classification_output_is_valid():
    result = llm.analyze_sentiment("This product is amazing!")
    assert result.lower() in ["positive", "very positive", "overwhelmingly positive"]
```

**Strategy 4 — Statistical testing:** Run N times and verify consistency exceeds a threshold:

```python
def test_classification_consistency(n_runs=10, min_rate=0.8):
    results = [llm.classify("My order hasn't arrived") for _ in range(n_runs)]
    success_rate = sum("support" in r.lower() for r in results) / n_runs
    assert success_rate >= min_rate
```

---

## 2. Integration testing agent component interactions

Integration testing verifies that agent components work correctly together — LLM with tools, retriever with generator, agents with memory, and agents with other agents. The key technique is the **record-and-replay pattern**, which captures real interactions once and replays them deterministically.

### The record-and-replay pattern for LLM + tool integration

Block Engineering's approach (January 2026) has become a best practice: record real MCP server interactions and LLM responses to fixture files, then replay them deterministically in CI. Tests assert **tool call sequences and interaction flow**, not exact output text:

```python
# Recording mode: captures real interactions to fixture files
provider = TestProvider.new_recording(real_provider, "fixtures/session.json")
response, usage = await provider.complete(system, messages, tools)
provider.finish_recording()

# Replay mode: deterministic, no network calls
provider = TestProvider.new_replaying("fixtures/session.json")
response, usage = await provider.complete(system, messages, tools)
```

VCR.py provides a similar pattern for Python HTTP-based tests, recording API calls to cassette files:

```python
@pytest.fixture(scope="session")
def vcr_config():
    return {"filter_headers": [("authorization", "XXXX"), ("x-api-key", "XXXX")]}

@pytest.mark.vcr()
def test_weather_agent():
    result = agent.invoke({"messages": [HumanMessage(content="Weather in SF?")]})
    assert "weather" in result["messages"][-1].content.lower()
```

### Testing RAG pipelines with the RAG triad metrics

RAG integration testing centers on three core metrics — the **RAG Triad** — evaluating retrieval quality, faithfulness, and answer relevance together:

```python
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric, AnswerRelevancyMetric, ContextualRelevancyMetric
)

def test_rag_pipeline():
    query = "What is the refund policy?"
    actual_output = rag_pipeline(query)
    
    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        expected_output="Refunds available within 30 days of purchase.",
        retrieval_context=["Policy: All customers eligible for 30-day full refund."]
    )
    assert_test(test_case, [
        FaithfulnessMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7),
        ContextualRelevancyMetric(threshold=0.7),
    ])
```

**FaithfulnessMetric** extracts claims from the output and checks each against the retrieval context: `Faithfulness = Truthful Claims / Total Claims`. **AnswerRelevancyMetric** measures whether the response addresses the input question. **ContextualRelevancyMetric** evaluates whether retrieved documents are relevant to the query. Together, these three metrics catch the most critical RAG failure modes: hallucination, off-topic answers, and poor retrieval.

### Contract testing with Pydantic schemas

Pydantic models serve as strict contracts between LLM output and tool inputs, failing early on wrong data types or missing required fields:

```python
from pydantic import BaseModel, ValidationError

class FlightSearchInput(BaseModel):
    origin: str
    destination: str
    date: str  # ISO format
    passengers: int = 1

def test_tool_input_contract():
    """Verify LLM-generated arguments conform to tool schema."""
    llm_output = {"origin": "SFO", "destination": "JFK", "date": "2025-03-15"}
    validated = FlightSearchInput(**llm_output)
    assert validated.passengers == 1  # Default applied

def test_tool_rejects_invalid_input():
    with pytest.raises(ValidationError):
        FlightSearchInput(origin="SFO")  # Missing required fields
```

### Testing multi-agent communication

Multi-agent integration tests should verify handoff correctness, role clarity, and input/output format compatibility between agents:

- **Handoff tests**: Does the delegating agent correctly route tasks to the receiving agent?
- **Prompt sensitivity**: Does changing tone or syntax affect handover success?
- **Schema alignment**: Are the output formats of one agent compatible with the input expectations of the next?
- **Reviewer patterns**: A "reviewer agent" validates results from other agents against expected quality metrics.

### Component-level evaluation with DeepEval's @observe

DeepEval's `@observe` decorator enables attaching metrics to specific components within a larger agent, allowing targeted integration testing:

```python
from deepeval.tracing import observe, update_current_span
from deepeval.test_case import LLMTestCase
from deepeval.metrics import ToolCorrectnessMetric, ArgumentCorrectnessMetric
from deepeval import evaluate
from deepeval.dataset import Golden

tool_correctness = ToolCorrectnessMetric(threshold=0.7)
argument_correctness = ArgumentCorrectnessMetric()

@observe(type="tool")
def search_flights(origin, destination, date):
    return [{"id": "FL123", "price": 450}, {"id": "FL456", "price": 380}]

@observe(metrics=[tool_correctness], type="llm")
def llm_component(query):
    # LLM decides which tools to call
    update_current_span(test_case=LLMTestCase(
        input=query,
        actual_output="Found 2 flights",
        tools_called=[ToolCall(name="search_flights")],
        expected_tools=[ToolCall(name="search_flights")]
    ))
    return search_flights("SFO", "JFK", "2025-03-15")

@observe()
def travel_agent(input_text):
    return llm_component(input_text)

evaluate(
    observed_callback=travel_agent,
    goldens=[Golden(input="Find flights from SFO to JFK on March 15")]
)
```

The `@observe` decorator creates **spans** in a trace. The collection of spans forms the full trace. Each span can have metrics attached for component-level scoring, while end-to-end metrics evaluate the entire trace.

---

## 3. System testing complete agent workflows

System testing evaluates whether the entire agent accomplishes its intended task end-to-end. This is the most expensive testing layer but also the most directly tied to business value.

### End-to-end task completion evaluation

DeepEval's **TaskCompletionMetric** analyzes the full execution trace to determine whether the agent achieved its goal:

```python
from deepeval.tracing import observe, update_current_trace
from deepeval.dataset import Golden, EvaluationDataset
from deepeval.metrics import (
    TaskCompletionMetric, StepEfficiencyMetric,
    PlanQualityMetric, PlanAdherenceMetric
)

@observe()
def trip_planner_agent(input):
    @observe(type="tool")
    def restaurant_finder(city):
        return ["Le Jules Verne", "Angelina Paris", "Septime"]

    @observe(type="tool")
    def itinerary_generator(destination, days):
        return ["Eiffel Tower", "Louvre Museum"][:days]

    destination, days = "Paris", 2
    itinerary = itinerary_generator(destination, days)
    restaurants = restaurant_finder(destination)
    output = f"Itinerary: {itinerary}, Restaurants: {restaurants}"
    update_current_trace(input=input, output=output)
    return output

dataset = EvaluationDataset(goldens=[
    Golden(input="Plan a 2-day trip to Paris with restaurant recommendations")
])

# End-to-end metrics analyze the full agent trace
task_completion = TaskCompletionMetric(threshold=0.7, model="gpt-4o")
step_efficiency = StepEfficiencyMetric()
plan_quality = PlanQualityMetric(threshold=0.7)
plan_adherence = PlanAdherenceMetric()

for golden in dataset.evals_iterator(
    metrics=[task_completion, step_efficiency, plan_quality, plan_adherence]
):
    trip_planner_agent(golden.input)
```

**TaskCompletionMetric** computes `AlignmentScore(Task, Outcome)` by extracting the inferred task and actual outcome from the trace. **StepEfficiencyMetric** flags agents that complete tasks but waste resources on redundant steps — a high TaskCompletion score with a low StepEfficiency score means the agent works but needs optimization. **PlanQualityMetric** and **PlanAdherenceMetric** work as a pair: quality checks whether the plan is logical and complete, while adherence checks whether the agent actually follows its own plan.

### Multi-turn conversation testing

Multi-turn testing validates that agents maintain coherence, context, and correctness across extended interactions:

```python
from deepeval.test_case import Turn, ConversationalTestCase

convo_test = ConversationalTestCase(
    turns=[
        Turn(role="user", content="I need to return shoes I bought last week"),
        Turn(role="assistant", content="I can help with that. What's your order number?",
             retrieval_context=["Return policy: 30-day window, order number required"]),
        Turn(role="user", content="It's ORDER-12345"),
        Turn(role="assistant", content="I've initiated a return for ORDER-12345. "
             "You'll receive a full refund within 5-7 business days.",
             retrieval_context=["Refund processing: 5-7 business days for full refund"]),
    ]
)
```

LangWatch's **Scenario** framework takes a simulation-based approach where realistic goal-driven users interact with agents across multiple turns, testing binary outcomes: "Can the agent help a customer cancel their order when they don't remember their order number?"

Anthropic's guidance on multi-turn evals emphasizes that **mistakes compound** in agent loops — an incorrect tool call in turn 3 can cascade into completely wrong behavior by turn 10. Evals should explicitly encode expected behavior to resolve ambiguity.

### Red teaming and safety testing with DeepTeam

**DeepTeam** (by Confident AI, open-source under Apache 2.0) provides automated red teaming with **80+ vulnerability types** and **20+ attack methods**:

```python
from deepteam import red_team
from deepteam.vulnerabilities import Bias, Toxicity, PIILeakage
from deepteam.attacks.single_turn import PromptInjection, ROT13

async def model_callback(input: str, turns=None) -> str:
    # Your agent's response function
    return await your_agent.respond(input)

risk_assessment = red_team(
    model_callback=model_callback,
    vulnerabilities=[
        Bias(types=["race", "gender"]),
        Toxicity(types=["insults", "threats"]),
        PIILeakage(types=["api_and_database_access"]),
    ],
    attacks=[PromptInjection(weight=2), ROT13(weight=1)]
)
```

DeepTeam v1.1+ introduces **agentic red teaming** with 16 specialized vulnerabilities across five critical areas: direct control hijacking (authority spoofing, role manipulation), goal redirection, tool misuse and exploitation (recursive calls, budget exhaustion), cross-context injection, and memory poisoning.

For CI/CD integration, DeepTeam supports YAML configuration:

```yaml
models:
  simulator: gpt-3.5-turbo-0125
  evaluation: gpt-4o
target:
  purpose: "Customer support AI assistant"
  model: gpt-3.5-turbo
default_vulnerabilities:
  - name: "Bias"
    types: ["religion", "gender"]
  - name: "PIILeakage"
    types: ["api_and_database_access"]
```

Run via CLI: `deepteam run config.yaml`

DeepTeam also integrates with established frameworks like **OWASP ASI 2026** and **NIST AI Risk Management Framework**:

```python
from deepteam.frameworks import OWASP_ASI_2026
risk_assessment = red_team(model_callback=callback, framework=OWASP_ASI_2026())
```

### Performance and latency benchmarks

AI agent performance testing differs fundamentally from traditional load testing because processing is probabilistic and each session grows heavier as context accumulates. Key benchmarks for **2025**:

- **Simple queries**: P50 < 500ms, P95 < 1,000ms
- **Complex workflows**: P50 < 2s, P95 < 4s
- **Multi-agent orchestration**: P50 < 3s, P95 < 6s
- **Time-to-first-token (TTFT)**: Aim for < 500ms for conversational flow

Track **prompt tokens and completion tokens independently**, monitor context window utilization (≥90% means one message from truncation), and calculate cost per task across your test suite. Multi-turn tests are essential because they expose accumulation patterns that single-shot tests miss entirely.

---

## 4. Practical implementation with DeepEval

### Core test case structure

Every DeepEval evaluation starts with an `LLMTestCase`:

```python
from deepeval.test_case import LLMTestCase, ToolCall

test_case = LLMTestCase(
    input="What if these shoes don't fit?",                          # Required
    actual_output="We offer a 30-day full refund at no extra cost.", # Required
    expected_output="You're eligible for a 30-day refund.",          # Optional
    context=["All customers eligible for 30-day full refund."],      # Optional (ground truth)
    retrieval_context=["Only shoes can be refunded."],               # Optional (RAG docs)
    tools_called=[ToolCall(name="WebSearch")],                       # Optional
    expected_tools=[ToolCall(name="WebSearch")],                     # Optional
)
```

### Complete metrics reference with code examples

**G-Eval — custom criteria evaluation (most versatile metric):**

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

correctness = GEval(
    name="Correctness",
    criteria="Determine whether the actual output is factually correct "
             "based on the expected output.",
    evaluation_params=[
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.EXPECTED_OUTPUT
    ],
    threshold=0.5
)

# With explicit evaluation steps for more control:
compliance = GEval(
    name="Regulatory Compliance",
    evaluation_steps=[
        "Check if any regulated terms are used incorrectly",
        "Verify required disclaimers are present",
        "Ensure no unauthorized financial advice is given"
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
)
```

G-Eval implements the methodology from Liu et al. (EMNLP 2023): it uses **Auto-CoT** to decompose evaluation criteria into structured steps, then weights scores by token log-probabilities for fine-grained scoring. It achieved the highest Spearman correlation with human judgments (**0.514**) on summarization benchmarks.

**HallucinationMetric — detecting fabricated content:**

```python
from deepeval.metrics import HallucinationMetric

metric = HallucinationMetric(threshold=0.5, model="gpt-4.1")
test_case = LLMTestCase(
    input="What was the blond doing?",
    actual_output="A blond drinking water in public.",
    context=["A man with blond hair and brown shirt drinking from a public fountain."]
)
```

**FaithfulnessMetric — RAG grounding verification:**

```python
from deepeval.metrics import FaithfulnessMetric

metric = FaithfulnessMetric(threshold=0.7, model="gpt-4.1", include_reason=True)
test_case = LLMTestCase(
    input="What if these shoes don't fit?",
    actual_output="We offer a 30-day full refund at no extra cost.",
    retrieval_context=["All customers are eligible for a 30-day full refund."]
)
# Calculates: Truthful Claims / Total Claims
```

**ToolCorrectnessMetric — verifying tool selection:**

```python
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import ToolCall

metric = ToolCorrectnessMetric(threshold=0.7, model="gpt-4.1")
test_case = LLMTestCase(
    input="What if these shoes don't fit?",
    actual_output="We offer a 30-day full refund.",
    tools_called=[ToolCall(name="WebSearch"), ToolCall(name="ToolQuery")],
    expected_tools=[ToolCall(name="WebSearch")],
)
# Calculates: Correctly Used Tools / Total Tools Called
```

### LLM tracing with @observe

The `@observe` decorator creates a trace tree for evaluation. Each decorated function becomes a **span**; the collection of spans forms the **trace**:

```python
from openai import OpenAI
from deepeval.tracing import observe, update_current_trace

@observe()
def llm_app(query: str) -> str:
    @observe(type="retriever")
    def retriever(query: str) -> list[str]:
        chunks = vector_db.similarity_search(query, k=3)
        update_current_trace(retrieval_context=chunks)
        return chunks

    @observe(type="llm")
    def generator(query: str, context: list[str]) -> str:
        res = OpenAI().chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Context: {context}\n\nQ: {query}"}]
        ).choices[0].message.content
        update_current_trace(input=query, output=res)
        return res

    return generator(query, retriever(query))
```

Tracing is **non-intrusive** — it won't affect production code or add meaningful latency. The `type` parameter (`"agent"`, `"llm"`, `"tool"`, `"retriever"`) helps DeepEval understand the trace structure.

### Synthetic dataset generation

DeepEval's `Synthesizer` provides four methods for generating evaluation datasets:

```python
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import EvolutionConfig, Evolution
from deepeval.dataset import EvaluationDataset

synthesizer = Synthesizer()

# Method 1: From documents (PDF, DOCX, TXT)
goldens = synthesizer.generate_goldens_from_docs(
    document_paths=['knowledge_base.pdf', 'faq.docx'],
    include_expected_output=True
)

# Method 2: From pre-prepared contexts
goldens = synthesizer.generate_goldens_from_contexts(
    contexts=[
        ["Earth revolves around the Sun.", "Planets are celestial bodies."],
        ["Water freezes at 0°C.", "Chemical formula for water is H2O."],
    ],
    include_expected_output=True,
    max_goldens_per_context=2
)

# Method 3: From scratch (no source material needed)
goldens = synthesizer.generate_goldens_from_scratch(num_goldens=10)

# Method 4: Evolve existing goldens for more complexity
evolution_config = EvolutionConfig(
    evolutions={
        Evolution.REASONING: 1/4,
        Evolution.MULTICONTEXT: 1/4,
        Evolution.CONCRETIZING: 1/4,
        Evolution.CONSTRAINED: 1/4
    },
    num_evolutions=4
)
synthesizer = Synthesizer(evolution_config=evolution_config)
goldens = synthesizer.generate_goldens_from_goldens(
    goldens=existing_goldens, max_goldens_per_golden=2
)

# Save and push datasets
dataset = EvaluationDataset(goldens=goldens)
dataset.push(alias="Customer Support Eval v2")     # Cloud (Confident AI)
dataset.save_as(file_type="json", directory="./data")  # Local
```

### Pytest integration pattern

```python
# test_chatbot.py
import pytest
from deepeval import assert_test
from deepeval.metrics import GEval, AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.dataset import EvaluationDataset, Golden

def test_answer_correctness():
    metric = GEval(
        name="Correctness",
        criteria="Determine if actual output is factually correct based on expected output.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT]
    )
    test_case = LLMTestCase(
        input="What is the capital of France?",
        actual_output=my_agent("What is the capital of France?"),
        expected_output="Paris"
    )
    assert_test(test_case, [metric])  # Use assert_test, NEVER evaluate() inside tests

# Parametrized tests from datasets
dataset = EvaluationDataset(goldens=[
    Golden(input="What's the refund policy?"),
    Golden(input="How do I track my order?"),
])
for golden in dataset.goldens:
    dataset.add_test_case(LLMTestCase(
        input=golden.input,
        actual_output=my_agent(golden.input)
    ))

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_customer_chatbot(test_case: LLMTestCase):
    assert_test(test_case, [AnswerRelevancyMetric(threshold=0.5)])
```

Run with: `deepeval test run test_chatbot.py -n 4 -c` (parallel + cached).

---

## 5. The testing pyramid reimagined for AI agents

The traditional testing pyramid collapses for AI agents because the assumption of deterministic input → output breaks. Three influential formulations have emerged, all organized by **uncertainty tolerance** rather than traditional test types.

**Block Engineering's four-layer pyramid** (Angie Jones, January 2026) provides the most practical framework:

| Layer | What it tests | Speed/Cost | Deterministic? |
|-------|--------------|------------|----------------|
| **Base: Deterministic foundations** | Tool schemas, retry logic, delegation, parsers | Fast, free | ✅ Yes |
| **Middle: Reproducible reality** | Record/replay of real LLM+tool interactions | Fast, free (after recording) | ✅ Yes |
| **Upper: Probabilistic performance** | Structured benchmarks run multiple times | Slow, moderate cost | ⚠️ Statistical |
| **Top: Vibes and judgment** | LLM-as-judge with rubrics, 3 runs + majority vote | Slowest, highest cost | ❌ No |

The critical decision: **don't run live LLM tests in CI**. CI validates deterministic layers only. Benchmarks run on demand, not on every pull request.

**LangWatch/Scenario's three-layer pyramid** maps testing layers to their function: unit tests (foundation) for API connections and data pipelines, evals and optimization (middle) for RAG accuracy and prompt tuning, and simulations (peak) for multi-turn conversation testing that maps directly to business value.

**Recommended ratio**: Many fast deterministic unit tests at the base (**~70%**), moderate integration tests using record/replay or mocks (**~20%**), and fewer but critical end-to-end simulations (**~10%**) for business-value validation. The exact ratio depends on your agent's complexity — agents with many tools need more integration tests, while simple chatbots need more unit tests for prompt quality.

---

## 6. CI/CD pipeline integration

### GitHub Actions configuration

```yaml
name: AI Agent Test Suite
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -e ".[test]"
      - name: Run deterministic unit tests
        run: pytest tests/unit/ -v  # No API keys needed

  eval-tests:
    runs-on: ubuntu-latest
    needs: unit-tests  # Only run if unit tests pass
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -e ".[test]"
      - name: Login to Confident AI
        env:
          CONFIDENT_API_KEY: ${{ secrets.CONFIDENT_API_KEY }}
        run: deepeval login --confident-api-key "$CONFIDENT_API_KEY"
      - name: Run DeepEval tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: deepeval test run tests/eval/ -n 4 -c
```

### Cost control strategies for CI

- Use **cheaper evaluation models** (`gpt-4o-mini` instead of `gpt-4o`) for CI runs
- DeepEval's `-c` (cache) flag skips previously evaluated test cases
- Configure local models via Ollama for free evaluation: `deepeval set-ollama --model=llama3`
- Run expensive benchmarks **on-demand** (manual trigger), not on every PR
- Use the **down-model pattern**: validate logic on smaller models first, then confirm on production models before release

### Regression testing workflow

The Confident AI platform automatically tracks metric scores across test runs when `CONFIDENT_API_KEY` is set. Log hyperparameters for A/B comparison:

```python
import deepeval

@deepeval.log_hyperparameters(model="gpt-4o", prompt_template="v2.3")
def test_with_tracking():
    assert_test(test_case, [metric])
```

Datasets preserve golden ordering for consistent regression testing. The recommended cycle: evaluate offline → deploy → monitor online → collect failure cases → add to offline dataset → refine → repeat.

### Production monitoring

Production monitoring uses **referenceless metrics** (no expected output available) on live interactions. DeepEval's `@observe` decorator traces production calls non-intrusively, sending data to Confident AI for quality dashboards. Key production metrics to track: response quality (faithfulness, hallucination rates), operational metrics (latency, throughput), cost (tokens per request), and user satisfaction (thumbs up/down, escalation rates).

---

## 7. Advanced topics

### LLM-as-a-Judge: methodology and limitations

LLM-as-a-Judge uses a powerful LLM to evaluate outputs from other LLM systems. Strong LLM judges (GPT-4 class) achieve **80-90% agreement** with human evaluators, comparable to inter-annotator agreement between humans. However, several biases require mitigation:

- **Verbosity bias**: LLMs favor longer responses regardless of quality
- **Self-preference bias**: Models prefer outputs from similar architectures
- **Position bias**: In pairwise comparisons, systematic preference for first or second response
- **Domain gaps**: In expert domains like medicine or law, LLM-human agreement drops to **60-68%**

Mitigations include using structured rubrics, decomposing complex criteria into binary yes/no questions, requesting chain-of-thought reasoning, running **multiple evaluations with majority voting** (3 runs, tiebreaker on 4th), and calibrating against human annotations.

### Building custom metrics

DeepEval provides three levels of custom metric complexity:

**Level 1 — G-Eval** (simplest): Define criteria in plain English:

```python
tone_metric = GEval(name="Professional Tone",
    criteria="Rate whether the response maintains a professional, helpful tone.",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT])
```

**Level 2 — DAG metric** (deterministic decision trees): Build explicit evaluation paths with LLM judges at each node for more predictable scoring.

**Level 3 — BaseMetric** (full control): Implement any scoring logic:

```python
from deepeval.metrics import BaseMetric

class WordCountMetric(BaseMetric):
    def __init__(self, max_words=100, threshold=0.5):
        self.threshold = threshold
        self.max_words = max_words

    def measure(self, test_case: LLMTestCase) -> float:
        word_count = len(test_case.actual_output.split())
        self.score = max(0, 1 - (word_count - self.max_words) / self.max_words)
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)
```

### Evaluation dataset management

Start with **40-60 test cases**, grow to **150-300** as your agent matures. Load datasets from multiple sources:

```python
from deepeval.dataset import EvaluationDataset

dataset = EvaluationDataset()
dataset.pull(alias="Customer Support v3")            # From Confident AI
dataset.add_goldens_from_csv_file("edge_cases.csv", input_col_name="query")
dataset.add_goldens_from_json_file("regression.json", input_key_name="query")
```

Use **FiltrationConfig** with `synthetic_input_quality_threshold` to ensure generated data meets quality bars. Mine production logs monthly for new failure patterns, convert them to test cases, and refresh your suite. Research from CMU shows that **75%** of production teams evaluate without formal benchmark sets, relying on A/B testing and user feedback — formal golden datasets provide a significant quality advantage over this common but suboptimal practice.

### Snapshot testing for prompt regression

Track prompt changes across deployments with layered checks: deterministic (exact matches, JSON schema compliance), semantic (embedding similarity, fact coverage), and judge-based (LLM evaluator scoring). Store configuration metadata — prompt version, model ID, parameters, RAG snapshot hash — with every test run. Block merges if pass rate drops below **90%** or any safety test fails.

---

## Conclusion

Testing AI agents requires a fundamentally different mindset from traditional software testing. The most important shift is **organizing by uncertainty tolerance**: deterministic tests (tool schemas, parsers, prompt templates) form the fast, cheap base; record-and-replay integration tests provide reproducible verification of real interactions; probabilistic benchmarks run on-demand with statistical aggregation; and LLM-as-judge evaluation with structured rubrics sits at the top for subjective quality assessment.

DeepEval has emerged as the dominant open-source framework, providing **50+ metrics** across three categories: agentic metrics (TaskCompletion, ToolCorrectness, ArgumentCorrectness, PlanQuality, PlanAdherence, StepEfficiency), RAG metrics (Faithfulness, AnswerRelevancy, Hallucination, ContextualRelevancy), and custom metrics (G-Eval, DAG, BaseMetric). Its `@observe` decorator enables component-level evaluation without modifying production code, and its pytest integration brings LLM evaluation into standard CI/CD workflows.

Three practical principles should guide implementation: **never run live LLM calls in CI** (use mocks and recorded responses for speed, cost, and determinism), **mock at the unit level but evaluate at the integration level** (unit tests verify logic, evaluation tests verify quality), and **treat red teaming as continuous** (convert every red-team finding into a regression test). Start with a small golden dataset, grow it from production failures, and track metrics over time — the compound effect of consistent measurement is the single most powerful lever for improving AI agent quality.