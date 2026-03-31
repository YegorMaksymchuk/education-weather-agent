# Makefile: venv (OS-aware), deps, run with PROMPT_VERSION, tests by level
# Usage: make help | make install | make run | make test-no-llm | etc.

# --- OS detection and venv paths ---
ifeq ($(OS),Windows_NT)
  VENV_BIN := venv/Scripts
  VENV_PYTHON := $(VENV_BIN)/python.exe
  VENV_PIP := $(VENV_BIN)/pip.exe
  PY ?= python
else
  VENV_BIN := venv/bin
  VENV_PYTHON := $(VENV_BIN)/python
  VENV_PIP := $(VENV_BIN)/pip
  PY ?= python3
endif

PROMPT_VERSION ?= 2

# Docker image name (override: make docker-build DOCKER_IMAGE=my-agent:v1)
DOCKER_IMAGE ?= weather-agent:latest

.PHONY: help venv install install-prod run run-prompt-1 run-prompt-2
.PHONY: test test-no-llm test-with-otel-export test-with-otel-llm test-coverage
.PHONY: test-unit-mock test-unit-llm test-integration-mock test-integration-llm test-system-mock test-system-llm
.PHONY: lint lint-fix code-security dependency-security ci historical-build
.PHONY: docker-build docker-run docker-up docker-down docker-logs
.PHONY: observability-up observability-down observability-logs observability-verify run-with-otel
.PHONY: clean

help:
	@echo "Targets:"
	@echo "  venv              Create virtualenv (OS-aware)"
	@echo "  install           Create venv + install deps + dev deps"
	@echo "  install-prod      Create venv + install prod deps only"
	@echo "  run               Run bot (PROMPT_VERSION=$(PROMPT_VERSION)); override: make run PROMPT_VERSION=1"
	@echo "  run-prompt-1      Run bot with PROMPT_VERSION=1"
	@echo "  run-prompt-2      Run bot with PROMPT_VERSION=2"
	@echo "  run-prompt-3      Run bot with PROMPT_VERSION=3"
	@echo "  test              Run all tests"
	@echo "  test-no-llm       Run tests that do not need OPENAI_API_KEY (UnitMock, UnitLLM, IntegrationMock, SystemMock)"
	@echo "  test-with-otel-export  test-no-llm + IntegrationLLM + SystemLLM with OTLP (needs OPENAI_API_KEY for LLM dirs)"
	@echo "  test-with-otel-llm  IntegrationLLM + SystemLLM only with OTLP (real OpenAI; fills GenAI dashboard panels)"
	@echo "  test-coverage     Run test-no-llm with coverage report"
	@echo "  test-unit-mock    Run tests/UnitMock/"
	@echo "  test-unit-llm     Run tests/UnitLLM/"
	@echo "  test-integration-mock  Run tests/IntegrationMock/"
	@echo "  test-integration-llm   Run tests/IntegrationLLM/ (needs OPENAI_API_KEY)"
	@echo "  test-system-mock  Run tests/SystemMock/"
	@echo "  test-system-llm   Run tests/SystemLLM/ (needs OPENAI_API_KEY)"
	@echo "  lint              Ruff check + format check (same as CI)"
	@echo "  lint-fix          Ruff check --fix + format"
	@echo "  code-security     Bandit scan on src/"
	@echo "  dependency-security  pip-audit on installed deps"
	@echo "  historical-build  Build ChromaDB index from data/chunks.csv (requires OPENAI_API_KEY)"
	@echo "  ci                lint + code-security + dependency-security + test-no-llm"
	@echo "  docker-build      Build Docker image ($(DOCKER_IMAGE))"
	@echo "  docker-run        Run container with --env-file .env (read-only, tmpfs /tmp)"
	@echo "  docker-up         docker compose up -d"
	@echo "  docker-down       docker compose down"
	@echo "  docker-logs       docker compose logs -f"
	@echo "  observability-up  Start ClickHouse, OTel Collector, Grafana (docker compose)"
	@echo "  observability-down docker compose down"
	@echo "  observability-logs Follow otel-collector logs"
	@echo "  observability-verify  Row count + sample SpanAttributes keys in ClickHouse (stack must be up)"
	@echo "  run-with-otel     Run bot with OTLP to localhost:4318 (start observability-up first)"
	@echo "  clean             Remove venv, __pycache__, .pytest_cache"

venv:
	$(PY) -m venv venv

install: venv
	$(VENV_PIP) install -r requirements.txt
	$(VENV_PIP) install -e ".[dev]"

install-prod: venv
	$(VENV_PIP) install -r requirements.txt

run: install
	PROMPT_VERSION=$(PROMPT_VERSION) $(VENV_PYTHON) main.py

run-prompt-1: install
	PROMPT_VERSION=1 $(VENV_PYTHON) main.py

run-prompt-2: install
	PROMPT_VERSION=2 $(VENV_PYTHON) main.py

run-prompt-3: install
	PROMPT_VERSION=3 $(VENV_PYTHON) main.py

test: install
	$(VENV_PYTHON) -m pytest tests/ -v

test-no-llm: install
	$(VENV_PYTHON) -m pytest tests/UnitMock/ tests/UnitLLM/ tests/IntegrationMock/ tests/SystemMock/ -v

# Export traces/metrics to local OTLP (e.g. make observability-up). Service name in Grafana: weather-agent-tests.
# Includes IntegrationLLM + SystemLLM so spans include full gen_ai.* (model, tokens, cost) when OPENAI_API_KEY is set.
test-with-otel-export: install
	OTEL_TESTS_EXPORT=1 \
	OTEL_EXPORTER_OTLP_ENDPOINT=$${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4318} \
	OTEL_SERVICE_NAME=$${OTEL_SERVICE_NAME:-weather-agent-tests} \
	OTEL_DEPLOYMENT_ENVIRONMENT=$${OTEL_DEPLOYMENT_ENVIRONMENT:-test} \
	$(VENV_PYTHON) -m pytest tests/UnitMock/ tests/UnitLLM/ tests/IntegrationMock/ tests/SystemMock/ tests/IntegrationLLM/ tests/SystemLLM/ -v

# Real LLM tests only — best for filling all GenAI Cost Dashboard panels (ChatOpenAI spans with model/tokens/cost).
test-with-otel-llm: install
	OTEL_TESTS_EXPORT=1 \
	OTEL_EXPORTER_OTLP_ENDPOINT=$${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4318} \
	OTEL_SERVICE_NAME=$${OTEL_SERVICE_NAME:-weather-agent-tests} \
	OTEL_DEPLOYMENT_ENVIRONMENT=$${OTEL_DEPLOYMENT_ENVIRONMENT:-test} \
	$(VENV_PYTHON) -m pytest tests/IntegrationLLM/ tests/SystemLLM/ -v

test-coverage: install
	$(VENV_PYTHON) -m pytest tests/UnitMock/ tests/UnitLLM/ tests/IntegrationMock/ tests/SystemMock/ -v --cov=src/weather_agent --cov-report=term-missing

test-unit-mock: install
	$(VENV_PYTHON) -m pytest tests/UnitMock/ -v

test-unit-llm: install
	$(VENV_PYTHON) -m pytest tests/UnitLLM/ -v

test-integration-mock: install
	$(VENV_PYTHON) -m pytest tests/IntegrationMock/ -v

test-integration-llm: install
	$(VENV_PYTHON) -m pytest tests/IntegrationLLM/ -v

test-system-mock: install
	$(VENV_PYTHON) -m pytest tests/SystemMock/ -v

test-system-llm: install
	$(VENV_PYTHON) -m pytest tests/SystemLLM/ -v

# --- Lint and security (mirror CI) ---
lint: install
	$(VENV_PYTHON) -m ruff check .
	$(VENV_PYTHON) -m ruff format --check .

lint-fix: install
	$(VENV_PYTHON) -m ruff check . --fix
	$(VENV_PYTHON) -m ruff format .

code-security: install
	$(VENV_PIP) install bandit
	$(VENV_PYTHON) -m bandit -r src/ -ll

dependency-security: install
	$(VENV_PIP) install pip-audit
	$(VENV_PYTHON) -m pip_audit

ci: lint code-security dependency-security test-no-llm

historical-build: install
	$(VENV_PYTHON) -c "from langchain_openai import OpenAIEmbeddings; from weather_agent.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, OPENAI_EMBEDDING_MODEL; from weather_agent.historical.store import build_and_persist_chroma; emb = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL); build_and_persist_chroma('data/chunks.csv', CHROMA_PERSIST_DIR, emb, collection_name=CHROMA_COLLECTION_NAME); print('Built ChromaDB collection', CHROMA_COLLECTION_NAME, 'in', CHROMA_PERSIST_DIR, 'from data/chunks.csv')"

# --- Docker ---
docker-build:
	docker build -t $(DOCKER_IMAGE) .

docker-run: docker-build
	docker run --rm --read-only --tmpfs /tmp --env-file .env $(DOCKER_IMAGE)

docker-up: docker-build
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# --- Observability (OpenLIT → OTLP Collector → ClickHouse → Grafana) ---
observability-up:
	docker compose up -d clickhouse otel-collector grafana

observability-down:
	docker compose down

observability-logs:
	docker compose logs -f otel-collector

# Quick sanity check: traces present and whether any gen_ai.* keys exist on a sample row.
observability-verify:
	docker compose exec -T clickhouse clickhouse-client -q "SELECT count() AS trace_rows, max(Timestamp) AS max_ts FROM otel.otel_traces"
	@echo "--- gen_ai.* keys on latest span (empty if no rows or no GenAI instrumentation) ---"
	docker compose exec -T clickhouse clickhouse-client -q "SELECT arrayFilter(k -> startsWith(k, 'gen_ai'), mapKeys(SpanAttributes)) AS gen_ai_keys FROM otel.otel_traces ORDER BY Timestamp DESC LIMIT 1"

run-with-otel: install
	OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 \
	OTEL_SERVICE_NAME=weather-agent \
	OTEL_DEPLOYMENT_ENVIRONMENT=development \
	PROMPT_VERSION=$(PROMPT_VERSION) $(VENV_PYTHON) main.py

clean:
	rm -rf venv .pytest_cache
	-find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	-find . -type f -name '*.pyc' -delete 2>/dev/null || true
