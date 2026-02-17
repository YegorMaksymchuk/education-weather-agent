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

.PHONY: help venv install install-prod run run-prompt-1 run-prompt-2
.PHONY: test test-no-llm test-coverage
.PHONY: test-unit-mock test-unit-llm test-integration-mock test-integration-llm test-system-mock test-system-llm
.PHONY: clean

help:
	@echo "Targets:"
	@echo "  venv              Create virtualenv (OS-aware)"
	@echo "  install           Create venv + install deps + dev deps"
	@echo "  install-prod      Create venv + install prod deps only"
	@echo "  run               Run bot (PROMPT_VERSION=$(PROMPT_VERSION)); override: make run PROMPT_VERSION=1"
	@echo "  run-prompt-1      Run bot with PROMPT_VERSION=1"
	@echo "  run-prompt-2      Run bot with PROMPT_VERSION=2"
	@echo "  test              Run all tests"
	@echo "  test-no-llm       Run tests that do not need OPENAI_API_KEY (UnitMock, UnitLLM, IntegrationMock, SystemMock)"
	@echo "  test-coverage     Run test-no-llm with coverage report"
	@echo "  test-unit-mock    Run tests/UnitMock/"
	@echo "  test-unit-llm     Run tests/UnitLLM/"
	@echo "  test-integration-mock  Run tests/IntegrationMock/"
	@echo "  test-integration-llm   Run tests/IntegrationLLM/ (needs OPENAI_API_KEY)"
	@echo "  test-system-mock  Run tests/SystemMock/"
	@echo "  test-system-llm   Run tests/SystemLLM/ (needs OPENAI_API_KEY)"
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

test: install
	$(VENV_PYTHON) -m pytest tests/ -v

test-no-llm: install
	$(VENV_PYTHON) -m pytest tests/UnitMock/ tests/UnitLLM/ tests/IntegrationMock/ tests/SystemMock/ -v

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

clean:
	rm -rf venv .pytest_cache
	-find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	-find . -type f -name '*.pyc' -delete 2>/dev/null || true
