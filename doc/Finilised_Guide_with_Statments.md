# The complete guide to testing AI agents in 2025

**AI agent testing requires a fundamentally new testing paradigm.** Traditional software produces deterministic outputs; agents combine non-deterministic LLM reasoning with deterministic tool execution, memory persistence, and multi-step orchestration. The modern approach layers four distinct testing levels — unit, integration, tools, and system — each targeting different failure modes with purpose-built frameworks. PydanticAI's TestModel, LangChain's GenericFakeChatModel, DeepEval's 50+ metrics, testcontainers for real infrastructure, and simulation frameworks like LangWatch Scenario now form the core toolkit. This report provides actionable patterns, concrete code examples, and decision frameworks across all four layers.

---

## 1. Unit testing: fast, deterministic, zero-API-cost

Unit testing for AI agents focuses on isolating individual components — LLM calls, tool functions, prompt templates, parsers, and validators — and verifying them without real API calls. The cardinal rule: **every commit triggers unit tests that complete in seconds, never hitting a live LLM**.

### Mocking LLM responses with framework-native fakes

PydanticAI provides the most sophisticated test infrastructure. Its `TestModel` generates data satisfying JSON schemas procedurally (no AI involved), while `FunctionModel` lets you write custom response logic:

```python
import pytest
from pydantic_ai import models, Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel, AgentInfo

models.ALLOW_MODEL_REQUESTS = False  # Global safety guard — blocks real API calls

agent = Agent('openai:gpt-4o', output_type=str)

async def test_with_test_model():
    with agent.override(model=TestModel(custom_output_text='Sunny skies ahead')):
        result = await agent.run('Weather in London?')
        assert result.output == 'Sunny skies ahead'

def custom_responder(messages, info: AgentInfo):
    if info.function_tools:
        return ModelResponse(parts=[ToolCallPart(
            tool_name='weather_forecast',
            args={'location': 'London', 'date': '2025-03-15'}
        )])
    return ModelResponse(parts=[TextPart('Sunny with rain')])

async def test_with_function_model():
    with agent.override(model=FunctionModel(custom_responder)):
        result = await agent.run('Weather in London?')
```

LangChain offers `GenericFakeChatModel` for mocking both text responses and tool calls, and `FakeListChatModel` for simple sequential responses:

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolCall

model = GenericFakeChatModel(messages=iter([
    AIMessage(content="", tool_calls=[
        ToolCall(name="get_weather", args={"city": "SF"}, id="call_1")
    ]),
    "It's 72°F and sunny in SF."
]))
```

For raw OpenAI client code, standard `unittest.mock` works but sits at a lower abstraction level — prefer framework-native fakes when available, as they're more resilient to API changes.

### Testing non-deterministic outputs with property-based and semantic approaches

LLM outputs vary across runs. Three strategies handle this without asserting exact strings.

**Property-based testing with Hypothesis** validates structural invariants:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=500))
def test_json_parser_never_crashes(raw_text):
    """Parser should return dict or raise ValueError — never crash."""
    try:
        result = my_json_parser(raw_text)
        assert isinstance(result, dict)
    except ValueError:
        pass
```

**Semantic similarity assertions** compare meaning rather than exact strings, using sentence embeddings:

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

def assert_semantically_similar(text1, text2, threshold=0.8):
    embeddings = model.encode([text1, text2])
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    assert sim >= threshold, f"Similarity {sim:.3f} below {threshold}"
```

**Statistical consistency testing** runs the same prompt N times and checks pairwise similarity distributions, catching unstable prompts that produce wildly varying outputs.

### Snapshot testing catches prompt drift cheaply

The `inline-snapshot` library (used by the Pydantic team and OpenAI Agents SDK) auto-generates expected values directly in source code. Paired with `dirty-equals` for dynamic fields, it's the gold standard for prompt template regression:

```python
from inline_snapshot import snapshot
from dirty_equals import IsStr, IsNow

def test_system_prompt():
    prompt = build_system_prompt(role="admin", context="sales")
    assert prompt == snapshot(
        "You are a helpful sales assistant with admin privileges."
    )

def test_agent_trace():
    trace = run_agent_and_get_trace()
    assert trace == snapshot({
        "agent_name": "weather_bot",
        "timestamp": IsNow(),
        "run_id": IsStr(),
        "tools_called": ["weather_forecast"],
    })
```

Running `pytest --inline-snapshot=fix` auto-populates snapshots; `--inline-snapshot=update` refreshes changed values. The alternative `syrupy` stores snapshots in separate `.ambr` files, better suited for large data structures.

### Testing structured output parsing

Pydantic models serve as both the output schema and the validation layer. Test parsers with valid data, boundary conditions, and deliberately malformed LLM output:

```python
from pydantic import BaseModel, Field, ValidationError

class WeatherResponse(BaseModel):
    location: str
    temperature: float = Field(ge=-100, le=150)
    conditions: str

def test_rejects_impossible_temperature():
    with pytest.raises(ValidationError):
        WeatherResponse(location="Mars", temperature=999, conditions="sunny")

def test_extracts_json_from_markdown_wrapper():
    text = 'Here is the result:\n```json\n{"location": "London"}\n```'
    assert extract_json_from_llm_response(text) == {"location": "London"}
```

PydanticAI's `TestModel` auto-generates data matching Pydantic schemas, validating that your output type constraints work end-to-end without any LLM call.

### Unit testing best practices at a glance

- **Set `ALLOW_MODEL_REQUESTS = False` globally** in `conftest.py` to prevent accidental real API calls
- **Test tool functions in isolation** — they're just Python functions with standard test patterns
- **Test output validators directly** — PydanticAI validators, guardrails, and PII filters are pure functions
- **Use `InMemorySaver`** (LangGraph) instead of real databases for stateful unit tests
- **Reserve DeepEval's LLM-as-judge metrics** for eval pipelines, not fast unit tests — they require real LLM calls

---

## 2. Integration testing with testcontainers and recorded responses

Integration testing verifies that agent components work together — LLM calls chained with real databases, vector stores, and external services. The modern approach combines **testcontainers for real infrastructure** with **VCR.py for deterministic LLM replay**.

### Testcontainers bring production-grade infrastructure to tests

The testcontainers-python library (v4.14+, acquired by Docker in 2023) provides **40+ specialized modules** including five AI-specific ones: `testcontainers[chroma]`, `testcontainers[qdrant]`, `testcontainers[weaviate]`, `testcontainers[milvus]`, and `testcontainers[ollama]`. These spin up real Docker containers for each test session.

A complete multi-service fixture for AI agent integration tests:

```python
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.chroma import ChromaContainer
from testcontainers.qdrant import QdrantContainer

@pytest.fixture(scope="session")
def ai_infrastructure():
    postgres = PostgresContainer("postgres:16-alpine")
    redis = RedisContainer("redis:7")
    chroma = ChromaContainer()
    qdrant = QdrantContainer("qdrant/qdrant:v1.8.3")

    postgres.start(); redis.start(); chroma.start(); qdrant.start()

    yield {
        "postgres_url": postgres.get_connection_url(),
        "redis_host": redis.get_container_host_ip(),
        "redis_port": redis.get_exposed_port(6379),
        "chroma_config": chroma.get_config(),
        "qdrant_client": qdrant.get_client(),
    }

    qdrant.stop(); chroma.stop(); redis.stop(); postgres.stop()
```

### Testing RAG pipelines against real vector databases

Mocked retrieval misses indexing bugs, distance metric misconfigurations, and filter expression failures. Real vector databases in testcontainers catch these:

```python
def test_rag_retrieval_with_real_qdrant(ai_infrastructure):
    client = ai_infrastructure["qdrant_client"]
    from qdrant_client.models import VectorParams, Distance

    client.create_collection(
        "knowledge_base",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    client.upsert("knowledge_base", points=[
        {"id": 1, "vector": [0.1]*384, "payload": {"text": "AI testing guide"}},
        {"id": 2, "vector": [0.9]*384, "payload": {"text": "Cooking recipes"}},
    ])

    results = client.search("knowledge_base", query_vector=[0.1]*384, limit=1)
    assert results[0].payload["text"] == "AI testing guide"

def test_rag_with_chromadb(ai_infrastructure):
    import chromadb
    cfg = ai_infrastructure["chroma_config"]
    client = chromadb.HttpClient(host=cfg["host"], port=cfg["port"])
    collection = client.get_or_create_collection("docs")

    collection.add(
        documents=["AI testing is critical", "Banana recipes"],
        ids=["doc1", "doc2"],
    )
    results = collection.query(query_texts=["testing AI systems"], n_results=1)
    assert "testing" in results["documents"][0][0].lower()
```

### Testing agent memory with real Redis and PostgreSQL

```python
def test_conversation_memory_persists(ai_infrastructure):
    import redis
    r = redis.Redis(
        host=ai_infrastructure["redis_host"],
        port=ai_infrastructure["redis_port"]
    )
    # Store conversation turns
    r.rpush("conv:user123", '{"role": "user", "content": "My name is Alice"}')
    r.rpush("conv:user123", '{"role": "assistant", "content": "Hello Alice!"}')

    # Verify retrieval across "sessions"
    history = r.lrange("conv:user123", 0, -1)
    assert len(history) == 2
    assert b"Alice" in history[0]
```

### VCR.py makes LLM calls deterministic in CI

VCR.py records HTTP interactions to YAML cassettes on first run, then replays them without network calls. Combined with `pytest-recording`, it requires minimal setup:

```python
# conftest.py
@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [("authorization", "REDACTED"), ("x-api-key", "REDACTED")],
    }

# test file
@pytest.mark.vcr
def test_agent_with_recorded_llm(ai_infrastructure):
    agent = MyAgent(config=ai_infrastructure)
    response = agent.process("What documents about testing?")
    assert response is not None
```

The `vcr-langchain` library extends this specifically for LangChain, while `baml_vcr` preserves type information for BAML-based applications. **Critical caveat**: always filter API keys from cassettes, and re-record when prompts or tools change.

### Mock LLM servers for development and testing

**MockLLM** (by Stacklok Labs) provides a YAML-configured server compatible with both OpenAI and Anthropic API formats, supporting streaming and configurable latency. For simpler needs, a FastAPI mock server takes ~20 lines of code and serves OpenAI-compatible responses at `localhost:8000`.

### Decision framework: when mocks beat testcontainers and vice versa

| Criterion | Use mocks/VCR | Use testcontainers |
|---|---|---|
| **Speed** | Milliseconds | Seconds (container startup) |
| **LLM responses** | Essential — VCR or fakes | Use Ollama container for local LLM |
| **Vector DB behavior** | Misses real similarity search bugs | Tests real indexing and distances |
| **Agent memory** | Misses persistence edge cases | Tests real Redis/PG persistence |
| **CI complexity** | No Docker required | Requires Docker-in-Docker |
| **Maintenance** | Cassettes go stale | Containers always fresh |

The recommended hybrid: **mock LLMs with framework fakes or VCR**, **use testcontainers for all infrastructure** (databases, vector stores, queues), and **run the Ollama testcontainer** when you need actual local model inference in CI.

### Contract testing between agent components

Pydantic models serve as lightweight contracts between agent modules. For formalized consumer-driven contracts across teams, Pact supports message-based contracts covering async agent communication:

```python
from pydantic import BaseModel

class AgentMessage(BaseModel):
    sender: str
    recipient: str
    task_id: str
    payload: dict
    timestamp: float

# Validated at every agent communication boundary
msg = AgentMessage(sender="planner", recipient="executor", ...)
```

---

## 3. Tools integration testing: verifying agents pick and use tools correctly

Tool selection and invocation is the most testable aspect of agent behavior. An agent that selects the right tool with wrong arguments, or the right arguments for the wrong tool, fails silently unless explicitly tested.

### DeepEval's ToolCorrectnessMetric and ArgumentCorrectnessMetric

**ToolCorrectnessMetric** compares `tools_called` against `expected_tools`, with options for ordering enforcement and exact matching:

```python
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import ToolCorrectnessMetric

test_case = LLMTestCase(
    input="What's the return policy for shoes?",
    actual_output="We offer 30-day full refunds.",
    tools_called=[ToolCall(name="WebSearch"), ToolCall(name="PolicyQuery")],
    expected_tools=[ToolCall(name="WebSearch"), ToolCall(name="PolicyQuery")],
)
metric = ToolCorrectnessMetric(
    should_consider_ordering=True,   # Enforce sequence
    should_exact_match=True,         # No extra tools allowed
)
evaluate(test_cases=[test_case], metrics=[metric])
```

**ArgumentCorrectnessMetric** is referenceless — it uses an LLM judge to evaluate whether arguments are logically correct given the input, without requiring pre-defined expected values:

```python
from deepeval.metrics import ArgumentCorrectnessMetric

metric = ArgumentCorrectnessMetric(threshold=0.7, model="gpt-4o", include_reason=True)
test_case = LLMTestCase(
    input="When did Trump first raise tariffs?",
    actual_output="Trump first raised tariffs in 2018.",
    tools_called=[
        ToolCall(
            name="WebSearch",
            description="Search for information on the web.",
            input={"search_query": "Trump first raised tariffs year"}
        )
    ]
)
evaluate(test_cases=[test_case], metrics=[metric])
```

The formula is straightforward: `Argument Correctness = Correctly Generated Parameters / Total Tool Calls`. When `available_tools` is supplied to ToolCorrectnessMetric, it additionally evaluates whether the tool selection was *optimal* among alternatives.

### Testing MCP server interactions

MCP (Model Context Protocol) testing is the newest frontier. Three approaches exist at increasing levels of sophistication.

**MCP Inspector** (official tool) provides visual debugging: `npx @modelcontextprotocol/inspector node build/index.js` opens an interactive UI for testing tools, resources, and prompts at `localhost:6274`.

**Automated testing with the official MCP client SDK** treats MCP primitives as contracts, similar to API endpoints. The pattern from Codely demonstrates comprehensive testing:

```typescript
describe("SearchCoursesByQuery MCP Tool", () => {
  const mcpClient = new Client(
    { name: "test-client", version: "1.0.0" },
    { capabilities: { tools: {}, resources: {}, prompts: {} } }
  );
  const transport = new StdioClientTransport({
    command: "npx", args: ["ts-node", "./src/mcp/server.ts"],
  });

  beforeAll(async () => { await mcpClient.connect(transport); });
  afterAll(async () => { await mcpClient.disconnect(); });

  it("lists the tool in available tools", async () => {
    const tools = await mcpClient.listTools();
    expect(tools.map(t => t.name)).toContain("courses-search_by_query");
  });

  it("returns empty array when no courses found", async () => {
    const response = await mcpClient.callTool("courses-search_by_query", {
      query: "nonexistent", languageCode: "en", limit: 5,
    });
    expect(response.isError).toBe(false);
    expect(response.structuredContent).toEqual({ courses: [] });
  });

  it("returns error for invalid input", async () => {
    await expect(
      mcpClient.readResource(`courses://invalid-id`)
    ).rejects.toThrow("not a valid nano id");
  });
});
```

For every MCP primitive, five tests are essential: **registration** (tool is exposed), **empty case** (no data), **happy path** (main flow), **error handling** (bad input), and **regression** (every bug gets a test).

### Testing tool error handling with simulation

The LangWatch Scenario framework enables testing agent resilience when tools fail:

```python
@pytest.mark.asyncio
async def test_tool_timeout_handling():
    with patch("my_agent.call_external_service") as mock_service:
        mock_service.side_effect = Exception("Request timeout")

        result = await scenario.run(
            name="tool timeout test",
            description="Test agent handles tool timeouts gracefully",
            agents=[ResilientAgent(), scenario.UserSimulatorAgent()],
            script=[
                scenario.user("Call the service at /api/data"),
                scenario.agent(),
                lambda state: mock_service.assert_called_once_with(endpoint="/api/data"),
                check_error_communicated,  # Verify agent told user about failure
                scenario.succeed(),
            ],
        )
        assert result.success
```

### Record-and-replay for tool interactions: Block Engineering's testing pyramid

Block Engineering (Angie Jones, January 2026) defined the AI agent testing pyramid with four layers, centered on record-and-replay at the critical middle tier:

1. **Deterministic foundations** — Unit tests with mock providers for retry logic, schema validation, turn limits
2. **Reproducible reality** — Record-and-replay for both LLM calls and MCP server interactions
3. **Probabilistic performance** — Benchmarks measuring success rates over multiple runs
4. **Vibes and judgment** — LLM-as-judge with rubrics, majority voting across 3 runs

Their record/replay implementation captures full provider interactions to fixture files. Recording mode wraps a real provider; replay mode needs no real provider at all. Docker's Cagent project takes a similar approach with a proxy-and-cassette model that normalizes volatile fields (IDs, timestamps) and auto-strips sensitive headers.

### LangGraph and CrewAI tool orchestration testing

For LangGraph agents, LangSmith's `create_trajectory_match_evaluator` validates tool call sequences in four modes — `strict` (identical order), `unordered` (all tools called), `subset` (minimum tools present), and `superset` (reference is subset of actual):

```python
from agentevals.trajectory.match import create_trajectory_match_evaluator

evaluator = create_trajectory_match_evaluator(trajectory_match_mode="superset")
result = agent.invoke({"messages": [HumanMessage(content="Weather in SF?")]})
evaluation = evaluator(
    outputs=result["messages"],
    reference_outputs=expected_trajectory
)
assert evaluation["score"] is True
```

CrewAI provides a built-in CLI: `crewai test -n 5 -m gpt-4o-mini` runs the crew for N iterations and reports performance metrics. For deeper testing, LangWatch Scenario adapters wrap both LangGraph and CrewAI agents.

---

## 4. System testing: end-to-end validation at scale

System testing evaluates complete agent workflows — from user input through reasoning, tool use, and final response — in production-like conditions. This is where task completion, safety, performance, and regression testing converge.

### Task completion with DeepEval's TaskCompletionMetric

The `TaskCompletionMetric` is the ultimate binary question: did the agent accomplish what the user asked? It extracts the task and outcome from traces, then uses an LLM judge to score alignment:

```python
from deepeval.tracing import observe
from deepeval.dataset import Golden, EvaluationDataset
from deepeval.metrics import TaskCompletionMetric

@observe(type="tool")
def search_flights(origin, destination, date):
    return [{"id": "FL123", "price": 450}, {"id": "FL456", "price": 380}]

@observe(type="tool")
def book_flight(flight_id):
    return {"confirmation": "CONF-789", "flight_id": flight_id}

@observe(type="agent")
def travel_agent(user_input):
    flights = search_flights("NYC", "LA", "2025-03-15")
    cheapest = min(flights, key=lambda x: x["price"])
    booking = book_flight(cheapest["id"])
    return f"Booked {cheapest['id']} for ${cheapest['price']}. Confirmation: {booking['confirmation']}"

task_metric = TaskCompletionMetric(threshold=0.7, model="gpt-4o")
dataset = EvaluationDataset(goldens=[
    Golden(input="Book the cheapest flight from NYC to LA")
])
for golden in dataset.evals_iterator(metrics=[task_metric]):
    travel_agent(golden.input)
```

Companion metrics — **StepEfficiencyMetric** (penalizes redundant steps), **PlanQualityMetric**, and **PlanAdherenceMetric** — provide diagnostic detail when task completion fails.

### Multi-turn conversation testing

DeepEval's `ConversationalTestCase` models multi-turn dialogues, with `ConversationSimulator` generating realistic test scenarios:

```python
from deepeval.test_case import ConversationalTestCase, Turn
from deepeval.metrics import ConversationalGEval
from deepeval.simulator import ConversationSimulator
from deepeval.dataset import ConversationalGolden

# Define scenario
golden = ConversationalGolden(
    scenario="Customer wants to purchase VIP concert tickets.",
    expected_outcome="Successful ticket purchase.",
    user_description="Impatient customer who wants quick resolution."
)

# Simulate conversation
async def chatbot_callback(input):
    return Turn(role="assistant", content=f"Response to: {input}")

simulator = ConversationSimulator(model_callback=chatbot_callback)
test_cases = simulator.simulate(conversational_goldens=[golden])

# Evaluate
metric = ConversationalGEval(
    name="Professionalism",
    criteria="Determine whether the assistant acted professionally.",
    threshold=0.5
)
evaluate(test_cases=test_cases, metrics=[metric])
```

Specialized multi-turn metrics include **KnowledgeRetentionMetric** (context carried across turns), **TurnRelevancyMetric**, and **MultiTurnMCPUseMetric** for tool usage in conversations.

### Red teaming with DeepTeam

**DeepTeam** (open-source, Apache 2.0) detects **80+ vulnerability types** using a multi-agent architecture (attacker, defender, evaluator). It supports OWASP Top 10 for LLMs, NIST AI RMF, and the OWASP Top 10 for Agentic Applications 2026:

```python
from deepteam import red_team
from deepteam.vulnerabilities import DirectControlHijacking
from deepteam.attacks.single_turn import AuthoritySpoofing

async def agent_callback(input: str) -> str:
    return my_agent.invoke(input)

risk_assessment = red_team(
    model_callback=agent_callback,
    vulnerabilities=[DirectControlHijacking()],
    attacks=[AuthoritySpoofing()]
)
```

For comprehensive framework-based assessment: `red_team(model_callback=callback, framework=OWASP_ASI_2026())` runs all agentic vulnerability categories including goal hijacking, tool misuse, cross-context injection, recursive tool calls, and unsafe tool composition. Attacks span both single-turn (prompt injection, jailbreaking) and multi-turn (linear escalation across up to 15 conversation turns).

### Simulation-based testing with LangWatch Scenario

LangWatch Scenario uses an "agent to test your agent" architecture — a **UserSimulatorAgent** generates realistic messages, a **JudgeAgent** evaluates against criteria, and your agent is tested in between:

```python
import scenario

@pytest.mark.agent_test
@pytest.mark.asyncio
async def test_customer_support_agent():
    result = await scenario.run(
        name="refund request handling",
        description="Frustrated customer wants a refund for a broken product.",
        agents=[
            SupportAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(criteria=[
                "Agent should empathize with the customer",
                "Agent should offer a refund within policy guidelines",
                "Agent should not make promises outside policy",
            ]),
        ],
        script=[
            scenario.user("I got a broken laptop and I want my money back!"),
            scenario.agent(),
            scenario.user(),  # Simulated follow-up
            scenario.agent(),
            scenario.judge(),  # Final evaluation
        ],
    )
    assert result.success
```

Scenario also supports **voice agent testing** with `RealtimeUserSimulatorAgent` that runs headlessly in CI, and provides `@scenario.cache()` for caching LLM calls across test runs.

### Performance and load testing are fundamentally different for agents

Traditional load tests simulate requests; AI agents require **conversation simulation**. Key metrics differ from standard APIs:

- **TTFT** (Time to First Token): Target <500ms for chatbots, <100ms for code completion
- **TPOT** (Time Per Output Token): Governs streaming smoothness
- **E2E latency**: A single complex query can cascade — retrieval (3.2s) → analysis (4.8s) → synthesis (8.3s) = **22 seconds, 8,400 tokens, $0.168**
- **Token consumption variability**: Identical requests may consume 50 or 5,000 tokens depending on reasoning path
- **Context window saturation**: 10 messages succeed; the 11th overflows and fails

**Gatling** provides LLM-specific load testing with token tracking and cost calculation. **LLM Locust** (TrueFoundry) extends Locust with async request generation and TTFT/inter-token latency metrics. The critical insight from practitioners: **use realistic prompts** (not random text) and **ramp gradually** — a single complex prompt can consume 100% GPU.

### Golden datasets and synthetic data generation

DeepEval's Synthesizer generates test data from four sources: documents, pre-chunked contexts, from scratch with styling configuration, and conversation simulation. Quality control filters synthetic inputs through clarity, depth, and relevance scoring:

```python
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import StylingConfig, FiltrationConfig

synthesizer = Synthesizer(
    styling_config=StylingConfig(
        input_format="Customer service questions",
        expected_output_format="Helpful support response",
        task="Answering e-commerce support queries",
    ),
    filtration_config=FiltrationConfig(
        synthetic_input_quality_threshold=0.8
    ),
)
goldens = synthesizer.generate_goldens_from_scratch(num_goldens=50)
```

Best practice: start with "silver" synthetic data, then promote to "gold" through subject-matter expert review. Check overlap with training corpora to avoid data contamination.

### CI/CD integration gates for agent quality

The standard pattern uses DeepEval or Scenario tests as merge-blocking gates in GitHub Actions:

```yaml
name: Agent Quality Gate
on: [pull_request]
jobs:
  agent-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install deepeval langwatch-scenario
      - name: Unit + Integration Tests (no LLM calls)
        run: pytest tests/unit tests/integration -m "not eval"
      - name: Agent Evaluations
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: deepeval test run tests/evals/
      - name: Scenario Simulations
        run: pytest tests/scenarios -m agent_test
```

Block Engineering's key insight: **"We don't run live LLM tests in CI. It's too expensive, too slow, and too flaky. CI validates the deterministic layers. Humans validate the rest when it matters."** The practical split: deterministic tests (unit, snapshot, integration with testcontainers + VCR) run on every commit; eval tests with real LLMs run on pre-release or nightly schedules.

---

## The testing strategy matrix ties it all together

| Layer | What it tests | Key tools | Run frequency | API calls? |
|---|---|---|---|---|
| **Unit** | Components in isolation | TestModel, GenericFakeChatModel, Hypothesis, inline-snapshot | Every commit | Never |
| **Integration** | Components working together | Testcontainers, VCR.py, MockLLM, Pact | Every PR | Recorded replay only |
| **Tools** | Tool selection, args, sequences | DeepEval metrics, MCP Inspector, Scenario | Every PR | LLM-as-judge only |
| **System** | End-to-end workflows | TaskCompletionMetric, Scenario, DeepTeam | Pre-release/nightly | Yes (LLM judges + target) |

## Conclusion

The four-layer testing approach reflects a fundamental truth about AI agents: **they are hybrid systems** combining deterministic code (testable traditionally) with non-deterministic reasoning (requiring new evaluation paradigms). The most mature teams separate these concerns cleanly. Unit and integration tests use framework-native fakes and testcontainers to achieve millisecond execution with zero API cost. Tool testing leverages DeepEval's reference-free metrics that evaluate argument correctness from context rather than expected values — a crucial insight since predetermined outputs rarely exist for agents. System testing embraces non-determinism through simulation (LangWatch Scenario), statistical evaluation (majority voting), and adversarial probing (DeepTeam).

The newest frontiers — **MCP contract testing** (treating protocol primitives like API endpoints) and **record-and-replay for agentic interactions** (Block Engineering's reproducible reality layer) — are rapidly maturing. The testcontainers ecosystem now covers every major vector database, and Ollama containers enable local LLM inference in CI. Together, these tools make comprehensive AI agent testing not just possible but practical, even for small teams running everything in GitHub Actions.